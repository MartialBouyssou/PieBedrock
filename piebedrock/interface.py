"""
interface.py — Bedrock login sequence handler.

Implements the full login/spawn flow for Minecraft Bedrock 1.21.x:

  Client → RequestNetworkSettings  (0xC1)
  Server → NetworkSettings          (0x8F)  [no compression yet]
  Client → Login                    (0x01)  [zlib compressed]
  Server → PlayStatus LOGIN_SUCCESS (0x02)
  Server → ResourcePacksInfo        (0x06)
  Client → ResourcePackClientResp   (0x08)  [HAVE_ALL_PACKS or COMPLETED]
  Server → ResourcePacksStack       (0x07)
  Client → ResourcePackClientResp   (0x08)  [COMPLETED]
  Server → StartGame                (0x0B)
  Server → BiomeDefinitionList      (0x7A)
  Server → AvailableEntityIdents    (0x77)
  Server → CreativeContent          (0x91)
  Server → PlayStatus PLAYER_SPAWN  (0x02)
"""

from pieraknet.packets.frame_set import FrameSetPacket

from piebedrock.buffer import BedrockBuffer
from piebedrock.codec import encode_packet, decode_packet, extract_packet_payload
from piebedrock.const import Packets

from piebedrock.packets.network_settings import NetworkSettingsPacket
from piebedrock.packets.play_status import PlayStatusPacket, PlayStatus
from piebedrock.packets.resource_packs_info import ResourcePacksInfoPacket
from piebedrock.packets.resource_packs_stack import ResourcePacksStackPacket
from piebedrock.packets.resource_pack_client_response import (
    ResourcePackClientResponsePacket, ResourcePackClientResponseStatus
)
from piebedrock.packets.start_game import StartGamePacket
from piebedrock.packets.biome_definition_list import BiomeDefinitionListPacket
from piebedrock.packets.available_entity_identifiers import AvailableEntityIdentifiersPacket
from piebedrock.packets.creative_content import CreativeContentPacket
from piebedrock.packets.login import LoginPacket


class GameInterface:
    def __init__(self, server):
        self.server = server
        # Per-connection state: address → dict
        self._state: dict = {}

    # ── Connection state helpers ───────────────────────────────────────────────

    def _get_state(self, connection) -> dict:
        key = connection.address
        if key not in self._state:
            self._state[key] = {"compress": False, "spawned": False}
        return self._state[key]

    def _set_compress(self, connection, value: bool):
        self._get_state(connection)["compress"] = value

    def _should_compress(self, connection) -> bool:
        return self._get_state(connection)["compress"]

    # ── Main entry-point called by PieRakNet ───────────────────────────────────

    def on_game_packet(self, frame, connection):
        body = frame['body'] if isinstance(frame, dict) else frame

        # Game packets always start with 0xFE
        if not body or body[0] != 0xFE:
            return

        try:
            inner = decode_packet(bytes(body))
            payload = extract_packet_payload(inner)
        except Exception as e:
            self.server.raknet.logger.warning(f"[PieBedrock] Failed to decode game packet: {e}")
            return

        if not payload:
            return

        # Read packet ID (14-bit VarInt header)
        buf = BedrockBuffer(payload)
        try:
            packet_id = buf.read_packet_id()
        except Exception:
            return

        self.server.raknet.logger.debug(f"[PieBedrock] Packet ID: 0x{packet_id:02X} from {connection.address}")

        # Route to the correct handler
        handlers = {
            Packets.REQUEST_NETWORK_SETTINGS_PACKET: self._handle_request_network_settings,
            Packets.LOGIN:                            self._handle_login,
            Packets.RESOURCE_PACK_CLIENT_RESPONSE:   self._handle_resource_pack_client_response,
            Packets.CLIENT_SERVER_HANDSHAKE:          self._handle_client_server_handshake,
        }

        handler = handlers.get(packet_id)
        if handler:
            # Pass remaining bytes after the packet-ID VarInt
            remaining = payload[buf.tell():]
            handler(remaining, connection)
        else:
            self.server.raknet.logger.debug(
                f"[PieBedrock] Unhandled packet 0x{packet_id:02X} from {connection.address}"
            )

    # ── Packet handlers ────────────────────────────────────────────────────────

    def _handle_request_network_settings(self, payload: bytes, connection):
        """Client says hello with its protocol version."""
        buf = BedrockBuffer(payload)
        try:
            protocol_version = buf.read_int_be()
        except Exception:
            protocol_version = 0

        logger = self.server.raknet.logger
        logger.info(f"[PieBedrock] RequestNetworkSettings — protocol {protocol_version} from {connection.address}")

        expected = self.server.raknet.game_protocol_version
        if protocol_version != expected:
            if protocol_version > expected:
                logger.warning(f"[PieBedrock] Client is newer ({protocol_version} > {expected}), sending anyway")
            else:
                logger.warning(f"[PieBedrock] Client is older ({protocol_version} < {expected})")
                self._send_play_status(connection, PlayStatus.FAILED_CLIENT, compress=False)
                return

        # Send NetworkSettings — NO compression yet (pre-login)
        pkt = NetworkSettingsPacket()
        pkt.compression_threshold = 0       # compress everything
        pkt.compression_method = 0x0000     # zlib
        pkt.client_throttle_enabled = False
        pkt.client_throttle_threshold = 0
        pkt.client_throttle_scalar = 0.0
        pkt.encode()

        self._send_raw(connection, encode_packet(pkt, compress=False))
        logger.info(f"[PieBedrock] → NetworkSettings sent (no compression)")

        # All subsequent packets will use zlib
        self._set_compress(connection, True)

    def _handle_login(self, payload: bytes, connection):
        """Decode login JWT chain, respond with login success and resource packs."""
        logger = self.server.raknet.logger

        pkt = LoginPacket(payload)
        try:
            pkt.decode_payload()
        except Exception as e:
            logger.error(f"[PieBedrock] Failed to decode Login packet: {e}")
            return

        logger.info(
            f"[PieBedrock] Login from {connection.address} — "
            f"player='{pkt.username}' uuid={pkt.uuid} xbox={pkt.is_xbox_authenticated}"
        )

        compress = self._should_compress(connection)

        # 1. PlayStatus: LOGIN_SUCCESS
        self._send_play_status(connection, PlayStatus.LOGIN_SUCCESS, compress)
        logger.info(f"[PieBedrock] → PlayStatus LOGIN_SUCCESS")

        # 2. ResourcePacksInfo (no packs)
        rpi = ResourcePacksInfoPacket()
        rpi.encode()
        self._send_raw(connection, encode_packet(rpi, compress))
        logger.info(f"[PieBedrock] → ResourcePacksInfo (empty)")

    def _handle_resource_pack_client_response(self, payload: bytes, connection):
        """Handle client's pack status and advance the login flow."""
        logger = self.server.raknet.logger
        compress = self._should_compress(connection)

        pkt = ResourcePackClientResponsePacket(payload)
        try:
            pkt.decode_payload()
        except Exception as e:
            logger.error(f"[PieBedrock] Failed to decode ResourcePackClientResponse: {e}")
            return

        logger.info(f"[PieBedrock] ResourcePackClientResponse status={pkt.status} from {connection.address}")

        if pkt.status == ResourcePackClientResponseStatus.HAVE_ALL_PACKS:
            # Send empty ResourcePacksStack
            rps = ResourcePacksStackPacket()
            rps.encode()
            self._send_raw(connection, encode_packet(rps, compress))
            logger.info(f"[PieBedrock] → ResourcePacksStack (empty)")

        elif pkt.status == ResourcePackClientResponseStatus.COMPLETED:
            # Client has all packs — spawn the player
            self._spawn_player(connection)

    def _handle_client_server_handshake(self, payload: bytes, connection):
        """Encryption handshake response — we skip encryption so this is a no-op."""
        self.server.raknet.logger.debug(f"[PieBedrock] ClientServerHandshake received (encryption not implemented)")

    # ── Spawn sequence ─────────────────────────────────────────────────────────

    def _spawn_player(self, connection):
        logger = self.server.raknet.logger
        compress = self._should_compress(connection)

        state = self._get_state(connection)
        if state.get("spawned"):
            return
        state["spawned"] = True

        # StartGame
        sg = StartGamePacket()
        sg.encode()
        self._send_raw(connection, encode_packet(sg, compress))
        logger.info(f"[PieBedrock] → StartGame")

        # BiomeDefinitionList
        bdl = BiomeDefinitionListPacket()
        bdl.encode()
        self._send_raw(connection, encode_packet(bdl, compress))
        logger.info(f"[PieBedrock] → BiomeDefinitionList")

        # AvailableEntityIdentifiers
        aei = AvailableEntityIdentifiersPacket()
        aei.encode()
        self._send_raw(connection, encode_packet(aei, compress))
        logger.info(f"[PieBedrock] → AvailableEntityIdentifiers")

        # CreativeContent
        cc = CreativeContentPacket()
        cc.encode()
        self._send_raw(connection, encode_packet(cc, compress))
        logger.info(f"[PieBedrock] → CreativeContent")

        # PlayStatus: PLAYER_SPAWN
        self._send_play_status(connection, PlayStatus.PLAYER_SPAWN, compress)
        logger.info(f"[PieBedrock] → PlayStatus PLAYER_SPAWN — player spawned!")

    # ── Sending helpers ────────────────────────────────────────────────────────

    def _send_play_status(self, connection, status: int, compress: bool = True):
        pkt = PlayStatusPacket()
        pkt.status = status
        pkt.encode()
        self._send_raw(connection, encode_packet(pkt, compress))

    def _send_raw(self, connection, body: bytes):
        """Wrap body in a RakNet FrameSet and send it."""
        frame_set = FrameSetPacket(self.server.raknet)
        frame_set.sequence_number = connection.server_sequence_number
        frame_set.create_frame(body, flags=0x00)   # unreliable
        connection.send_data(frame_set.encode())
