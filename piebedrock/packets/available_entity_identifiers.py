from piebedrock.packets.packet import BedrockPacket

# Packet ID: 0x77
# Direction: Server → Client
# NBT list of entity identifiers. Send minimal empty NBT compound.

_EMPTY_NBT = b'\x0a\x00\x00\x00'

class AvailableEntityIdentifiersPacket(BedrockPacket):
    PACKET_ID = 0x77
    PACKET_TYPE = "available_entity_identifiers"

    def __init__(self, data: bytes = b''):
        super().__init__(data)
        self.nbt_data: bytes = _EMPTY_NBT

    def encode_payload(self):
        self.write(self.nbt_data)
