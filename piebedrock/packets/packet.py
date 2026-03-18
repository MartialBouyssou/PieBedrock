import io
from piebedrock.buffer import BedrockBuffer


class BedrockPacket(BedrockBuffer):
    """
    Base class for all Bedrock game packets.

    Encoding layout (inside the RakNet frame body):
        0xFE                   — game packet marker
        VarInt (u32)           — total compressed payload length
        0x00 / 0xFF            — compression byte (0x00=zlib, 0xFF=none)
        [zlib-compressed or raw]
            VarInt (u32)       — inner payload length
            VarInt (u32 14bit) — packet header  (ID + subclient IDs)
            <payload bytes>

    For simplicity at this stage we do NOT compress (threshold=0 → always raw).
    The framing / compression wrapper is handled in codec.py.
    Here each subclass just fills its own payload bytes.
    """

    PACKET_ID: int = None
    PACKET_TYPE: str = None

    def __init__(self, data: bytes = b''):
        super().__init__(data)

    # ------------------------------------------------------------------
    # Header helpers
    # ------------------------------------------------------------------

    def encode_header(self):
        """Write the 14-bit packet-ID VarInt (+ 0x00 subclient padding)."""
        self.write_packet_id(self.PACKET_ID)

    def decode_header(self) -> int:
        return self.read_packet_id()

    # ------------------------------------------------------------------
    # encode / decode entry-points
    # ------------------------------------------------------------------

    def encode(self):
        """Encode header + payload into this buffer."""
        self.encode_header()
        if hasattr(self, 'encode_payload'):
            self.encode_payload()

    def decode(self):
        """Decode header + payload from this buffer."""
        self.decode_header()
        if hasattr(self, 'decode_payload'):
            self.decode_payload()

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def get_encoded_bytes(self) -> bytes:
        """Return the raw bytes written so far (without framing)."""
        return self.getvalue()
