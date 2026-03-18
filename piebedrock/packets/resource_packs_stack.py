from piebedrock.packets.packet import BedrockPacket

# Packet ID: 0x07
# Direction: Server → Client
# Always sent after ResourcePacksInfo. For a server with no packs, all lists empty.
# Reference: https://mojang.github.io/bedrock-protocol-docs/html/ResourcePackStackPacket.html

class ResourcePacksStackPacket(BedrockPacket):
    PACKET_ID = 0x07
    PACKET_TYPE = "resource_packs_stack"

    def __init__(self, data: bytes = b''):
        super().__init__(data)
        self.forced_to_accept: bool = False
        self.behavior_packs: list = []
        self.resource_packs: list = []
        self.game_version: str = "1.21.0"
        self.experiments: list = []
        self.experiments_previously_toggled: bool = False

    def encode_payload(self):
        self.write_bool(self.forced_to_accept)

        self.write_var_int(len(self.behavior_packs))
        for pack in self.behavior_packs:
            self.write_string(pack.get('uuid', ''))
            self.write_string(pack.get('version', ''))
            self.write_string(pack.get('sub_pack_name', ''))

        self.write_var_int(len(self.resource_packs))
        for pack in self.resource_packs:
            self.write_string(pack.get('uuid', ''))
            self.write_string(pack.get('version', ''))
            self.write_string(pack.get('sub_pack_name', ''))

        self.write_string(self.game_version)

        self.write_int(len(self.experiments))
        for exp in self.experiments:
            self.write_string(exp.get('name', ''))
            self.write_bool(exp.get('enabled', False))

        self.write_bool(self.experiments_previously_toggled)
