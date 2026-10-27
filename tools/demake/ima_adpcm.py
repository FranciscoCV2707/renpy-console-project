"""Codifica y decodifica muestras IMA-ADPCM en el formato de canal de Nintendo DS."""

from __future__ import annotations

_STEP_TABLE = (
    7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31,
    34, 37, 41, 45, 50, 55, 60, 66, 73, 80, 88, 97, 107, 118, 130, 143,
    157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408, 449, 494, 544,
    598, 658, 724, 796, 876, 963, 1060, 1166, 1282, 1411, 1552, 1707,
    1878, 2066, 2272, 2499, 2749, 3024, 3327, 3660, 4026, 4428, 4871,
    5358, 5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899,
    15289, 16818, 18500, 20350, 22385, 24623, 27086, 29794, 32767,
)
_INDEX_TABLE = (-1, -1, -1, -1, 2, 4, 6, 8)


def encode(samples: list[int] | tuple[int, ...]) -> bytes:
    """Codifica PCM signed 16-bit a header DS de 4 bytes y nibbles IMA-ADPCM."""
    if not samples:
        raise ValueError("se requiere al menos una muestra")
    if any(sample < -32768 or sample > 32767 for sample in samples):
        raise ValueError("las muestras deben ser PCM signed 16-bit")

    predictor = samples[0]
    index = 0
    output = bytearray(predictor.to_bytes(2, "little", signed=True))
    output.extend((index, 0))
    pending_nibble: int | None = None
    for sample in samples[1:]:
        step = _STEP_TABLE[index]
        difference = sample - predictor
        nibble = 8 if difference < 0 else 0
        difference = abs(difference)
        delta = step >> 3
        if difference >= step:
            nibble |= 4
            delta += step
        if difference >= step >> 1:
            nibble |= 2
            delta += step >> 1
        if difference >= step >> 2:
            nibble |= 1
            delta += step >> 2
        predictor += -delta if nibble & 8 else delta
        predictor = max(-32768, min(32767, predictor))
        index = max(0, min(88, index + _INDEX_TABLE[nibble & 7]))
        if pending_nibble is None:
            pending_nibble = nibble
        else:
            output.append(pending_nibble | (nibble << 4))
            pending_nibble = None
    if pending_nibble is not None:
        output.append(pending_nibble)
    output.extend(bytes((-len(output)) % 4))
    return bytes(output)


def decode(data: bytes, sample_count: int) -> list[int]:
    """Decodifica un flujo DS IMA-ADPCM con el número de muestras original."""
    if len(data) < 4 or len(data) % 4:
        raise ValueError("el flujo DS ADPCM debe incluir header y estar alineado a 4 bytes")
    if sample_count < 1 or sample_count > 1 + (len(data) - 4) * 2:
        raise ValueError("cantidad de muestras incompatible con el flujo")
    predictor = int.from_bytes(data[:2], "little", signed=True)
    index = data[2]
    if index > 88:
        raise ValueError("índice inicial IMA-ADPCM fuera de rango")
    samples = [predictor]
    for byte in data[4:]:
        for nibble in (byte & 0x0F, byte >> 4):
            if len(samples) == sample_count:
                return samples
            step = _STEP_TABLE[index]
            delta = step >> 3
            if nibble & 4:
                delta += step
            if nibble & 2:
                delta += step >> 1
            if nibble & 1:
                delta += step >> 2
            predictor += -delta if nibble & 8 else delta
            predictor = max(-32768, min(32767, predictor))
            index = max(0, min(88, index + _INDEX_TABLE[nibble & 7]))
            samples.append(predictor)
    return samples
