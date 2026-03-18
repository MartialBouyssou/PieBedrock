from piebedrock.packets.packet import BedrockPacket

# Packet ID: 0x08
# Direction: Client → Server
# Reference: https://mojang.github.io/bedrock-protocol-docs/html/ResourcePackClientResponsePacket.html

class ResourcePackClientResponseStatus:
    REFUSED         = 1
    SEND_PACKS      = 2
    HAVE_ALL_PACKS  = 3
    COMPLETED       = 4

class ResourcePackClientResponsePacket(BedrockPacket):
    PACKET_ID = 0x08
    PACKET_TYPE = "resource_pack_client_response"

    def __init__(self, data: bytes = b''):
        super().__init__(data)
        self.status: int = 0
        self.pack_ids: list = []

    def decode_payload(self):
        self.status = self.read_byte()
        count = self.read_unsigned_short()
        self.pack_ids = [self.read_string() for _ in range(count)]
