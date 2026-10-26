"""Tabla de perfiles de recursos por plataforma.

Cada entrada describe con datos la conversion que aplica el pipeline; el resto
del codigo lee de aqui para no tener valores fijos de una consola.
"""

from __future__ import annotations


PROFILES: dict[str, dict] = {
    "pc": {
        "name": "pc",
        "description": "PC: recursos originales, copiados tal cual.",
        "image_size": None,
        "audio_rate": None,
        "audio_channels": None,
        "skip_kinds": set(),
        "include_source": False,
        "include_skipped": False,
    },
    "psp": {
        "name": "psp",
        "description": "PSP: imagenes 480x272, audio WAV 22050 Hz mono; video omitido.",
        "image_size": (480, 272),
        "audio_rate": 22050,
        "audio_channels": 1,
        "skip_kinds": {"video"},
        "include_source": True,
        "include_skipped": True,
    },
    "ps2": {
        "name": "ps2",
        "description": "PS2: imagenes 640x448, audio WAV 44100 Hz estereo; video omitido.",
        "image_size": (640, 448),
        "audio_rate": 44100,
        "audio_channels": 2,
        "skip_kinds": {"video"},
        "include_source": True,
        "include_skipped": True,
    },
}
