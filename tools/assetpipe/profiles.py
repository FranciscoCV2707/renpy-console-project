"""Tabla de perfiles de recursos por plataforma.

Solo ``pc`` por ahora; el resto se agregan en tareas posteriores. La tabla esta
pensada para extenderse sin tocar el resto del pipeline: basta con agregar una
entrada.
"""

from __future__ import annotations


PROFILES: dict[str, dict] = {
    "pc": {
        "name": "pc",
        "description": "PC: recursos originales, copiados tal cual.",
    },
}
