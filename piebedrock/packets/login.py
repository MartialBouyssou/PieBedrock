import json
import base64
from piebedrock.packets.packet import BedrockPacket

# Packet ID: 0x01
# Direction: Client → Server
#
# Contains:
#   - protocol_version (Int BE) — deprecated but still present
#   - connection_request (String) — JSON with chain_data + client_data JWTs
#
# Reference: https://mojang.github.io/bedrock-protocol-docs/html/LoginPacket.html


def _b64_decode_jwt_payload(token: str) -> dict:
    """Decode the payload of a JWT without verifying the signature."""
    parts = token.split('.')
    if len(parts) < 2:
        return {}
    payload = parts[1]
    # Add padding
    payload += '=' * (-len(payload) % 4)
    try:
        return json.loads(base64.urlsafe_b64decode(payload))
    except Exception:
        return {}


class LoginPacket(BedrockPacket):
    PACKET_ID = 0x01
    PACKET_TYPE = "login"

    def __init__(self, data: bytes = b''):
        super().__init__(data)
        self.protocol_version: int = 0
        # Parsed fields (populated by decode_payload)
        self.username: str = "Player"
        self.xuid: str = ""
        self.uuid: str = ""
        self.chain_data: list = []
        self.client_data: dict = {}
        self.is_xbox_authenticated: bool = False
        # Raw strings
        self.raw_chain_data: str = ""
        self.raw_client_data: str = ""

    def decode_payload(self):
        # Protocol version is a Big-Endian int BEFORE the string
        self.protocol_version = self.read_int_be()

        # The rest is a single VarInt-prefixed string that contains a JSON object:
        # { "chain": [...JWTs...] }
        # followed immediately by another VarInt-prefixed JWT (client_data)
        connection_request = self.read_byte_array_var()
        cr_buf = type(self)(connection_request)  # reuse same class for reading

        # chain_data length (u32 LE)
        chain_len = cr_buf.read_unsigned_int()
        chain_json_bytes = cr_buf.read(chain_len)
        try:
            chain_obj = json.loads(chain_json_bytes.decode('utf-8'))
            self.chain_data = chain_obj.get('chain', [])
            self.raw_chain_data = chain_json_bytes.decode('utf-8')
        except Exception as e:
            print(f"[LoginPacket] Failed to parse chain data: {e}")
            self.chain_data = []

        # client_data length (u32 LE) + JWT string
        client_len = cr_buf.read_unsigned_int()
        client_jwt_bytes = cr_buf.read(client_len)
        self.raw_client_data = client_jwt_bytes.decode('utf-8')
        self.client_data = _b64_decode_jwt_payload(self.raw_client_data)

        # Extract player identity from chain JWTs
        self._parse_identity()

    def _parse_identity(self):
        """Extract username, UUID, XUID from the chain."""
        self.is_xbox_authenticated = len(self.chain_data) >= 3

        for jwt_token in self.chain_data:
            payload = _b64_decode_jwt_payload(jwt_token)
            extra = payload.get('extraData', {})
            if extra:
                self.username = extra.get('displayName', 'Player')
                self.xuid = extra.get('XUID', '')
                self.uuid = extra.get('identity', '')
                break

        # Fallback to client_data if chain gave nothing
        if self.username == 'Player' and self.client_data:
            self.username = self.client_data.get('ThirdPartyName', 'Player')
