"""Pipeline de recursos por plataforma (assetpipe).

Este paquete convierte (o, en el perfil PC, copia) los recursos de un juego
Ren'Py a la carpeta de salida de una plataforma y genera ``manifest.json``.
"""

from .manifest import run, inventory, build_manifest, copy_resources  # noqa: F401
from .profiles import PROFILES, get_profile  # noqa: F401

__all__ = [
    "PROFILES",
    "get_profile",
    "inventory",
    "build_manifest",
    "copy_resources",
    "run",
]