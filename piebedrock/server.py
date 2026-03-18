"""
server.py — BedrockServer entry-point.

Wraps PieRakNet's Server and attaches the GameInterface
that handles the Bedrock login/spawn protocol flow.

Protocol version 776 = Minecraft Bedrock 1.21.60
"""

from pieraknet.server import Server as RakNetServer
from piebedrock.interface import GameInterface


# Minecraft Bedrock 1.21.x protocol versions:
#   1.21.0  → 671
#   1.21.20 → 685
#   1.21.40 → 712
#   1.21.60 → 776
PROTOCOL_VERSION = 776
GAME_VERSION     = "1.21.60"


class BedrockServer:
    def __init__(
        self,
        hostname: str = "0.0.0.0",
        port: int = 19132,
        name: str = "PieMC Server",
        modt: str = "Powered by PieBedrock",
        max_players: int = 20,
    ):
        self.raknet = RakNetServer(
            hostname=hostname,
            port=port,
            ipv=4,
            game="MCPE",
            name=name,
            game_protocol_version=PROTOCOL_VERSION,
            version_name=GAME_VERSION,
            max_player_count=max_players,
            modt=modt,
        )
        self.interface = GameInterface(self)
        self.raknet.interface = self.interface

    def start(self):
        self.raknet.logger.info(
            f"[PieBedrock] Starting Bedrock server on "
            f"{self.raknet.hostname}:{self.raknet.port} "
            f"(MC {GAME_VERSION} / protocol {PROTOCOL_VERSION})"
        )
        self.raknet.start()

    def stop(self):
        self.raknet.logger.info("[PieBedrock] Stopping server...")
        self.raknet.stop()


if __name__ == '__main__':
    server = BedrockServer()
    server.start()
