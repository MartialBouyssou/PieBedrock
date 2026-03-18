"""
codec.py — Bedrock game-packet framing and compression.

Wire format inside a RakNet frame body:

    0xFE                        — Bedrock game-packet magic byte
    <inner bytes>               — one or more batched packets:

  Before NetworkSettings is sent (pre-login, no compression yet):
    0xFF                        — compression byte = "no compression"
    VarUInt                     — length of inner packet bytes
    <packet header + payload>   — raw, uncompressed

  After NetworkSettings (compression_threshold = 0 = always compress):
    0x00                        — compression byte = zlib
    <zlib compressed blob>      — decompresses to:
        VarUInt                 — length of inner packet bytes
        <packet header+payload>

For simplicity, this implementation uses NO compression for the
NetworkSettings packet itself (sent before compression is negotiated),
and ZLIB for all subsequent packets.
"""

import zlib
from piebedrock.buffer import BedrockBuffer

ALGO_ZLIB = 0x00
ALGO_NONE = 0xFF


def _encode_inner(packet) -> bytes:
    """Encode a BedrockPacket and prefix it with its VarInt length."""
    pkt_bytes = packet.getvalue()
    if not pkt_bytes:
        packet.encode()
        pkt_bytes = packet.getvalue()

    buf = BedrockBuffer()
    buf.write_var_int(len(pkt_bytes))
    buf.write(pkt_bytes)
    return buf.getvalue()


def encode_packet(packet, compress: bool = True) -> bytes:
    """
    Full pipeline: encode one packet → Bedrock frame body.

    Args:
        packet:   Configured BedrockPacket subclass (not yet encoded).
        compress: True = zlib (use after NetworkSettings handshake).
                  False = no compression (use for NetworkSettings itself).

    Returns:
        bytes to place directly in the RakNet frame body.
    """
    inner = _encode_inner(packet)

    out = BedrockBuffer()
    out.write_byte(0xFE)  # magic

    if compress:
        compressed = zlib.compress(inner, level=7)
        out.write_byte(ALGO_ZLIB)
        out.write(compressed)
    else:
        out.write_byte(ALGO_NONE)
        out.write(inner)

    return out.getvalue()


def decode_packet(data: bytes) -> bytes:
    """
    Strip the Bedrock frame wrapper.

    Args:
        data: Raw bytes from the RakNet frame body.

    Returns:
        Decompressed inner bytes (VarInt length + packet header + payload).

    Raises:
        ValueError on bad magic byte or unsupported compression.
    """
    buf = BedrockBuffer(data)

    magic = buf.read_byte()
    if magic != 0xFE:
        raise ValueError(f"Expected 0xFE magic, got 0x{magic:02X}")

    algo = buf.read_byte()
    blob = buf.read(buf.remaining())

    if algo == ALGO_ZLIB:
        try:
            return zlib.decompress(blob)
        except zlib.error as e:
            raise ValueError(f"zlib decompression failed: {e}")
    elif algo == ALGO_NONE:
        return blob
    else:
        raise ValueError(f"Unknown compression algorithm: 0x{algo:02X}")


def extract_packet_payload(inner: bytes) -> bytes:
    """
    Given inner bytes (VarInt length + payload), return just the payload.
    """
    buf = BedrockBuffer(inner)
    length = buf.read_var_int()
    return buf.read(length)
