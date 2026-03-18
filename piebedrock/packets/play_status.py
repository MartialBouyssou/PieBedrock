from piebedrock.packets.packet import BedrockPacket

# Packet ID: 0x02
# Direction: Server → Client
#
# Reference: https://mojang.github.io/bedrock-protocol-docs/html/PlayStatusPacket.html


class PlayStatus:
    LOGIN_SUCCESS       = 0
    FAILED_CLIENT       = 1   # "Outdated client!"
    FAILED_SERVER       = 2   # "Outdated server!"
    PLAYER_SPAWN        = 3   # Spawns the player in-world
    FAILED_INVALID_TENANT = 4
    FAILED_VANILLA_EDU  = 5
    FAILED_INCOMPATIBLE = 6
    FAILED_SERVER_FULL  = 7


class PlayStatusPacket(BedrockPacket):
    PACKET_ID = 0x02
    PACKET_TYPE = "play_status"

    def __init__(self, data: bytes = b''):
        super().__init__(data)
        self.status: int = PlayStatus.LOGIN_SUCCESS

    def encode_payload(self):
        self.write_int_be(self.status)

    def decode_payload(self):
        self.status = self.read_int_be()
