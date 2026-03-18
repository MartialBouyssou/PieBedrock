from piebedrock.packets.packet import BedrockPacket

# Packet ID: 0x7A
# Direction: Server → Client
# Sent after StartGame. Contains NBT-encoded biome definitions.
# For a minimal server we send the smallest valid NBT: an empty compound tag.
# Reference: https://mojang.github.io/bedrock-protocol-docs/html/BiomeDefinitionListPacket.html

# Minimal valid NBT: TAG_Compound("") { TAG_End }
_EMPTY_NBT = b'\x0a\x00\x00\x00'

class BiomeDefinitionListPacket(BedrockPacket):
    PACKET_ID = 0x7A
    PACKET_TYPE = "biome_definition_list"

    def __init__(self, data: bytes = b''):
        super().__init__(data)
        self.nbt_data: bytes = _EMPTY_NBT

    def encode_payload(self):
        self.write(self.nbt_data)
