from piebedrock.packets.packet import BedrockPacket

# Packet ID: 0x06
# Direction: Server → Client
#
# Sends metadata about available resource/behaviour packs.
# For a minimal server with no packs, all lists are empty.
#
# Reference: https://mojang.github.io/bedrock-protocol-docs/html/ResourcePacksInfoPacket.html


class ResourcePacksInfoPacket(BedrockPacket):
    PACKET_ID = 0x06
    PACKET_TYPE = "resource_packs_info"

    def __init__(self, data: bytes = b''):
        super().__init__(data)
        self.forced_to_accept: bool = False
        self.has_scripts: bool = False
        self.behavior_packs: list = []   # list of dicts
        self.resource_packs: list = []   # list of dicts

    def encode_payload(self):
        self.write_bool(self.forced_to_accept)
        self.write_bool(self.has_scripts)

        # Behaviour packs (u16 count)
        self.write_unsigned_short(len(self.behavior_packs))
        for pack in self.behavior_packs:
            self._encode_pack(pack)

        # Resource packs (u16 count)
        self.write_unsigned_short(len(self.resource_packs))
        for pack in self.resource_packs:
            self._encode_pack(pack)

    def _encode_pack(self, pack: dict):
        self.write_string(pack.get('uuid', ''))
        self.write_string(pack.get('version', ''))
        self.write_unsigned_long(pack.get('size', 0))
        self.write_string(pack.get('content_key', ''))
        self.write_string(pack.get('sub_pack_name', ''))
        self.write_string(pack.get('content_identity', ''))
        self.write_bool(pack.get('has_scripts', False))
