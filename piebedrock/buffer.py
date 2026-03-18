import struct
import uuid
from pieraknet.buffer import Buffer

# BedrockBuffer extends PieRakNet's Buffer but overrides methods that differ:
#
# PieRakNet Buffer uses:
#   - Big Endian for short, int, long  (!h, !i, !q)
#   - Short-prefixed (16-bit BE) strings
#   - Single-byte packet_id
#
# Bedrock Protocol uses:
#   - Little Endian for int, long, float  (<i, <q, <f)
#   - Big Endian only for specific fields (protocol_version, play_status)
#   - VarInt-prefixed UTF-8 strings
#   - 14-bit VarInt packet header
#
# Methods NOT overridden (PieRakNet's are correct):
#   write_byte / read_byte         (u8, identical)
#   write_bool / read_bool         (u8, identical)
#   write_ubyte / read_ubyte       (u8, identical)
#   write_uint24le / read_uint24le (LE 24-bit, correct)
#   write_var_int / read_var_int   (unsigned VarInt, same algorithm)
#   write_address / read_address   (RakNet addresses, not used in game packets)
#   remaining / feos               (buffer helpers, identical)


class BedrockBuffer(Buffer):

    # ── Short — Bedrock LE (overrides PieRakNet's BE) ─────────────────────────

    def read_short(self) -> int:
        return struct.unpack('<h', self.read(2))[0]

    def write_short(self, data: int):
        self.write(struct.pack('<h', int(data)))

    def read_unsigned_short(self) -> int:
        return struct.unpack('<H', self.read(2))[0]

    def write_unsigned_short(self, data: int):
        self.write(struct.pack('<H', int(data)))

    # Keep BE variants explicitly available for Bedrock fields that need them
    def read_short_be(self) -> int:
        return struct.unpack('>h', self.read(2))[0]

    def write_short_be(self, data: int):
        self.write(struct.pack('>h', int(data)))

    def read_unsigned_short_be(self) -> int:
        return struct.unpack('>H', self.read(2))[0]

    def write_unsigned_short_be(self, data: int):
        self.write(struct.pack('>H', int(data)))

    # ── Int — Bedrock LE (overrides PieRakNet's BE) ───────────────────────────

    def read_int(self) -> int:
        return struct.unpack('<i', self.read(4))[0]

    def write_int(self, data: int):
        self.write(struct.pack('<i', int(data)))

    def read_unsigned_int(self) -> int:
        return struct.unpack('<I', self.read(4))[0]

    def write_unsigned_int(self, data: int):
        self.write(struct.pack('<I', int(data)))

    # BE variants for specific Bedrock fields (protocol_version, play_status…)
    def read_int_be(self) -> int:
        return struct.unpack('>i', self.read(4))[0]

    def write_int_be(self, data: int):
        self.write(struct.pack('>i', int(data)))

    # ── Long — Bedrock LE (overrides PieRakNet's BE) ──────────────────────────

    def read_long(self) -> int:
        return struct.unpack('<q', self.read(8))[0]

    def write_long(self, data: int):
        self.write(struct.pack('<q', int(data)))

    def read_unsigned_long(self) -> int:
        return struct.unpack('<Q', self.read(8))[0]

    def write_unsigned_long(self, data: int):
        self.write(struct.pack('<Q', int(data)))

    # ── Float / Double — always LE in Bedrock ────────────────────────────────

    def read_float(self) -> float:
        return struct.unpack('<f', self.read(4))[0]

    def write_float(self, data: float):
        self.write(struct.pack('<f', float(data)))

    def read_double(self) -> float:
        return struct.unpack('<d', self.read(8))[0]

    def write_double(self, data: float):
        self.write(struct.pack('<d', float(data)))

    # ── VarInt unsigned — same algorithm as PieRakNet but with alias ──────────
    # PieRakNet already has read_var_int / write_var_int (unsigned).
    # We just add explicit aliases so callers can be explicit.

    def read_unsigned_var_int(self) -> int:
        return self.read_var_int()

    def write_unsigned_var_int(self, data: int):
        self.write_var_int(data)

    # ── VarInt signed (zigzag, NOT in PieRakNet) ──────────────────────────────

    def read_signed_var_int(self) -> int:
        n = self.read_var_int()
        return (n >> 1) ^ -(n & 1)

    def write_signed_var_int(self, data: int):
        n = (data << 1) ^ (data >> 31)
        self.write_var_int(n & 0xFFFFFFFF)

    # ── VarLong unsigned (NOT in PieRakNet) ───────────────────────────────────

    def read_var_long(self) -> int:
        value = 0
        shift = 0
        while True:
            byte = self.read(1)[0]
            value |= (byte & 0x7F) << shift
            if not (byte & 0x80):
                break
            shift += 7
            if shift >= 70:
                raise ValueError("VarLong too big")
        return value

    def write_var_long(self, data: int):
        data = data & 0xFFFFFFFFFFFFFFFF
        while True:
            byte = data & 0x7F
            data >>= 7
            if data:
                byte |= 0x80
            self.write(bytes([byte]))
            if not data:
                break

    def read_signed_var_long(self) -> int:
        n = self.read_var_long()
        return (n >> 1) ^ -(n & 1)

    def write_signed_var_long(self, data: int):
        n = (data << 1) ^ (data >> 63)
        self.write_var_long(n & 0xFFFFFFFFFFFFFFFF)

    # ── String — Bedrock VarInt-prefixed UTF-8 (overrides PieRakNet's short-prefixed ASCII) ──

    def read_string(self) -> str:
        length = self.read_var_int()
        return self.read(length).decode('utf-8')

    def write_string(self, data: str):
        encoded = data.encode('utf-8')
        self.write_var_int(len(encoded))
        self.write(encoded)

    # ── Packet ID — Bedrock 14-bit VarInt header (overrides PieRakNet's single byte) ──

    def read_packet_id(self) -> int:
        header = self.read_var_int()
        return header & 0x3FF  # lowest 10 bits = packet ID

    def write_packet_id(self, packet_id: int, sender: int = 0, target: int = 0):
        header = (packet_id & 0x3FF) | ((sender & 0x3) << 10) | ((target & 0x3) << 12)
        self.write_var_int(header)

    # ── Byte arrays with VarInt length prefix (NOT in PieRakNet) ─────────────

    def read_byte_array_var(self) -> bytes:
        length = self.read_var_int()
        return self.read(length)

    def write_byte_array_var(self, data: bytes):
        self.write_var_int(len(data))
        self.write(data)

    # ── Vectors ───────────────────────────────────────────────────────────────

    def read_vector3(self) -> tuple:
        return (self.read_float(), self.read_float(), self.read_float())

    def write_vector3(self, data: tuple):
        self.write_float(data[0])
        self.write_float(data[1])
        self.write_float(data[2])

    def read_vector2(self) -> tuple:
        return (self.read_float(), self.read_float())

    def write_vector2(self, data: tuple):
        self.write_float(data[0])
        self.write_float(data[1])

    # ── UUID (16 raw bytes) ───────────────────────────────────────────────────

    def read_uuid(self) -> uuid.UUID:
        return uuid.UUID(bytes=self.read(16))

    def write_uuid(self, data):
        if isinstance(data, uuid.UUID):
            self.write(data.bytes)
        else:
            self.write(uuid.UUID(str(data)).bytes)
