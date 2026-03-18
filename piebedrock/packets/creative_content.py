from piebedrock.packets.packet import BedrockPacket

# Packet ID: 0x91
# Direction: Server → Client
# Sent after StartGame. For a minimal server, send empty creative inventory.
# Reference: https://mojang.github.io/bedrock-protocol-docs/html/CreativeContentPacket.html

class CreativeContentPacket(BedrockPacket):
    PACKET_ID = 0x91
    PACKET_TYPE = "creative_content"

    def __init__(self, data: bytes = b''):
        super().__init__(data)
        self.items: list = []  # empty = no creative items

    def encode_payload(self):
        self.write_var_int(len(self.items))
        # Each item would be: write_var_int(net_id) + write_item_stack(item)
        # With empty list nothing is written — client accepts this fine
