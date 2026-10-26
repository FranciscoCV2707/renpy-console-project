"""Tabla de perfiles de recursos por plataforma.

Solo ``pc`` por ahora; el resto se agregan en tareas posteriores (T-504). La
tabla esta pensada para extenderse sin tocar el resto del pipeline: basta con
agregar una entrada y, si hace falta, un conversor en ``manifest.py``.
"""

from __future__ import annotations


# Tabla principal. Los valores son diccionarios para que sean faciles de
# serializar y de extender desde tests u otras herramientas.
PROFILES: dict[str, dict] = {
    "pc": {
        "name": "pc",
        "description": "PC: recursos originales, copiados tal cual.",
        "transform": "copy",
    },
}

# Alias por si alguien busca la tabla en minusculas.
profiles = PROFILES


def get_profile(name: str) -> dict | None:
    return PROFILES.get(name)


def list_profiles() -> list[str]:
    return sorted(PROFILES)


def is_known(name: str) -> bool:
    return name in PROFILES