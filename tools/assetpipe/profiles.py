"""Tabla de perfiles de recursos por plataforma.

``pc`` copia tal cual. Los demas reducen: imagenes que encajan en ``image_size`` (PNG),
audio a WAV PCM 16 bits con ``audio_rate`` y ``audio_channels``, y omiten los tipos de
``skip_kinds``.
"""

from __future__ import annotations


PROFILES: dict[str, dict] = {
    "pc": {
        "name": "pc",
        "description": "PC: recursos originales, copiados tal cual.",
    },
    "psp": {
        "name": "psp",
        "description": "PSP: imagenes en 480x272; audio >10 s en OGG Vorbis 44100 Hz estereo (q0), el resto WAV PCM 22050 Hz mono; sin video.",
        "image_size": (480, 272),
        "audio_rate": 22050,
        "audio_channels": 1,
        "music_rate": 44100,
        "music_channels": 2,
        "music_quality": 0,
        "music_threshold": 10,
        "skip_kinds": {"video"},
    },
    "ps2": {
        "name": "ps2",
        "description": "PS2: imagenes en 640x448; audio >10 s en OGG Vorbis 44100 Hz estereo (q2), el resto WAV PCM 22050 Hz mono; sin video.",
        "image_size": (640, 448),
        "audio_rate": 22050,
        "audio_channels": 1,
        "music_rate": 44100,
        "music_channels": 2,
        "music_quality": 2,
        "music_threshold": 10,
        "skip_kinds": {"video"},
    },
}
