from piebedrock.packets.packet import BedrockPacket

# Packet ID: 0x8F
# Direction: Server → Client
# Sent in response to RequestNetworkSettings (0xC1).
# Sets up compression for all subsequent packets.
#
# Reference: https://mojang.github.io/bedrock-protocol-docs/html/NetworkSettingsPacket.html

class NetworkSettingsPacket(BedrockPacket):
    PACKET_ID = 0x8F
    PACKET_TYPE = "network_settings"

    def __init__(self, data: bytes = b''):
        super().__init__(data)
        # Compress if packet size >= threshold bytes. 0 = always compress.
        self.compression_threshold: int = 0
        # 0x0000 = zlib, 0x0001 = snappy, 0xFFFF = none
        self.compression_method: int = 0x0000
        self.client_throttle_enabled: bool = False
        self.client_throttle_threshold: int = 0
        self.client_throttle_scalar: float = 0.0

    def encode_payload(self):
        self.write_unsigned_short(self.compression_threshold)
        self.write_unsigned_short(self.compression_method)
        self.write_bool(self.client_throttle_enabled)
        self.write_byte(self.client_throttle_threshold)
        self.write_float(self.client_throttle_scalar)
