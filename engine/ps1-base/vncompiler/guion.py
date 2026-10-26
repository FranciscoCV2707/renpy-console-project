"""Lectura de guion.json del kit (solo lectura): nodos de cada archivo, etiquetas de capitulo y hablantes."""
import json
import re
from pathlib import Path




def cargar(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def hijos(node):
    """Bloques anidados de un nodo, en el orden en que se ejecutan."""
    for key in ("body",):
        if node.get(key):
            yield node[key]
    for branch in node.get("branches") or []:
        yield branch.get("body") or []
    for choice in node.get("choices") or []:
        yield choice.get("body") or []


def buscar_etiqueta(guion, nombre):
    """Nodo `label` con ese nombre (en cualquier archivo) o None."""
    pila = list(guion["script"].values())
    while pila:
        nodos = pila.pop()
        for n in nodos:
            if n.get("op") == "label" and n.get("name") == nombre:
                return n
            pila.extend(hijos(n))
    return None


def capitulos(guion):
    """Etiquetas `chapter_*` en el orden de la historia (las de la pantalla de capitulos no cuentan)."""
    nombres = [k for k in guion.get("labels", {}) if k.startswith("chapter_") and k != "chapter_select"]
    return sorted(nombres, key=_clave)


def _clave(nombre):
    partes = nombre.removeprefix("chapter_").replace("_", ".")
    numero = "".join(c for c in partes.split(".")[0] if c.isdigit())
    return (int(numero) if numero else 0, nombre)


def hablantes(guion):
    """Variable de personaje -> id de hablante (1..N). El narrador es 0."""
    ids = {}
    next_id = 1
    for var, definition in guion.get("characters", {}).items():
        if definition.get("name") == "":
            ids[var] = 0
        else:
            ids[var] = next_id
            next_id += 1
    return ids


def speaker_table(guion, language="es"):
    ids = hablantes(guion)
    rows = [{"name": "", "color": [255, 255, 255]} for _ in range(max(ids.values(), default=0) + 1)]

    def image_name(match):
        definition = guion.get("images", {}).get(match.group(1), {})
        tree = definition.get("value", {}).get("tree", {})
        if tree.get("call") == "Text" and tree.get("args"):
            text = tree["args"][0]
            if text.get("call") == "_" and text.get("args"):
                text = text["args"][0]
            if isinstance(text.get("const"), str):
                return text["const"]
        raise ValueError(f"nombre de personaje sin resolver: {match.group(1)}")

    for var, definition in guion.get("characters", {}).items():
        if ids[var]:
            name = definition.get("tl", {}).get(language) or definition.get("name") or var
            rows[ids[var]]["name"] = re.sub(r"\{image=([^}]+)\}", image_name, name)
    return rows


def texto_es(node):
    """Texto en espanol de un `say`, o None si no tiene traduccion."""
    for entry in (node.get("tl", {}).get("es") or []):
        if entry.get("text"):
            return entry["text"]
    return None
