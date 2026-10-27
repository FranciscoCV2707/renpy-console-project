"""Compresor y descompresor del formato LZ77 0x10 de la BIOS de GBA."""

from __future__ import annotations

LZ77_WINDOW = 4096
LZ77_MIN_MATCH = 3
LZ77_MAX_MATCH = 18
LZ77_MAX_CHAIN = 128


def bios_lz77(data: bytes) -> bytes:
    """Codifica ``data`` con cabecera 0x10 y referencias de ventana de 4 KiB."""
    size = len(data)
    if size > 0xFFFFFF:
        raise ValueError(f"LZ77 de la BIOS: maximo 16 MiB, recibe {size} bytes")
    out = bytearray((0x10, size & 0xFF, (size >> 8) & 0xFF, (size >> 16) & 0xFF))
    head: dict[int, int] = {}
    prev = [-1] * size
    i = 0
    while i < size:
        flags = 0
        block = bytearray()
        for bit in range(7, -1, -1):
            if i >= size:
                break
            length, disp = _longest_match(data, i, size, head, prev)
            if length >= LZ77_MIN_MATCH:  # GBATEK: bit en 1 = bloque comprimido, en 0 = byte literal
                flags |= 1 << bit
                block.append(((length - LZ77_MIN_MATCH) << 4) | ((disp - 1) >> 8))
                block.append((disp - 1) & 0xFF)
                for pos in range(i, min(i + length, size - LZ77_MIN_MATCH + 1)):
                    _insert(data, head, prev, pos)
                i += length
            else:
                block.append(data[i])
                if i + LZ77_MIN_MATCH <= size:
                    _insert(data, head, prev, i)
                i += 1
        out.append(flags)
        out += block
    return bytes(out)


def bios_lz77_decompress(data: bytes) -> bytes:
    """Decodifica un flujo LZ77 tipo 0x10, rechazando entradas truncadas o inválidas."""
    if len(data) < 4 or data[0] != 0x10:
        raise ValueError("cabecera LZ77 tipo 0x10 invalida")
    size = int.from_bytes(data[1:4], "little")
    out = bytearray()
    pos = 4
    while len(out) < size:
        if pos >= len(data):
            raise ValueError("flujo LZ77 truncado antes de los flags")
        flags = data[pos]
        pos += 1
        for bit in range(7, -1, -1):
            if len(out) >= size:
                break
            if not flags & (1 << bit):
                if pos >= len(data):
                    raise ValueError("literal LZ77 truncado")
                out.append(data[pos])
                pos += 1
                continue
            if pos + 1 >= len(data):
                raise ValueError("referencia LZ77 truncada")
            token = (data[pos] << 8) | data[pos + 1]
            pos += 2
            length = (token >> 12) + LZ77_MIN_MATCH
            distance = (token & 0xFFF) + 1
            if distance > len(out):
                raise ValueError("referencia LZ77 anterior al inicio")
            for _ in range(length):
                if len(out) == size:
                    break
                out.append(out[-distance])
    return bytes(out)


def pack_4bpp(indices: bytes) -> bytes:
    """Empaqueta píxeles indexados a 4 bpp; el píxel izquierdo ocupa el nibble bajo."""
    out = bytearray((len(indices) + 1) // 2)
    for i in range(0, len(indices), 2):
        left = indices[i]
        right = indices[i + 1] if i + 1 < len(indices) else 0
        out[i // 2] = (right << 4) | left
    return bytes(out)


def _insert(data: bytes, head: dict[int, int], prev: list[int], pos: int) -> None:
    key = (data[pos] << 16) | (data[pos + 1] << 8) | data[pos + 2]
    prev[pos] = head.get(key, -1)
    head[key] = pos


def _longest_match(
    data: bytes, i: int, size: int, head: dict[int, int], prev: list[int]
) -> tuple[int, int]:
    if i + LZ77_MIN_MATCH > size:
        return 0, 0
    max_len = min(LZ77_MAX_MATCH, size - i)
    best_len, best_distance = 0, 0
    key = (data[i] << 16) | (data[i + 1] << 8) | data[i + 2]
    candidate = head.get(key, -1)
    low = i - LZ77_WINDOW
    chain = 0
    while candidate >= 0 and candidate >= low and chain < LZ77_MAX_CHAIN:
        if i - candidate < 2:  # LZ77UnCompVram escribe de 16 en 16 bits: distancia 1 no sirve (GBATEK)
            candidate = prev[candidate]
            continue
        length = LZ77_MIN_MATCH
        while length < max_len and data[candidate + length] == data[i + length]:
            length += 1
        if length > best_len:
            best_len, best_distance = length, i - candidate
            if length >= max_len:
                break
        candidate = prev[candidate]
        chain += 1
    return best_len, best_distance

