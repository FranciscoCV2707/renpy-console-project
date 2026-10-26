"""Enlaza etiquetas y comparte variables y ids de texto entre paquetes VNB1."""
from dataclasses import dataclass

from . import formatos, guion
from .compilar import Capitulo


def walk(nodes):
    for node in nodes:
        yield node
        for children in guion.hijos(node):
            yield from walk(children)


@dataclass
class Program:
    chapters: list
    variables: dict
    destinations: dict
    speakers: dict

    def write(self, output):
        output.mkdir(parents=True, exist_ok=True)
        for index, (vnb, texts, chapter) in enumerate(self.chapters):
            (output / f"C{index:02d}.VNB").write_bytes(vnb)
            (output / f"T{index:02d}.TXT").write_bytes(texts)


def compile_program(script, roots, text_layout=None):
    labels = {}
    owners = {}
    following = {}
    for nodes in script["script"].values():
        top_labels = [node for node in nodes if node.get("op") == "label"]
        for index, label in enumerate(top_labels):
            name = label["name"]
            labels[name] = label
            for nested in walk([label]):
                if nested.get("op") == "label":
                    owners[nested["name"]] = name
            body = label.get("body") or []
            if index + 1 < len(top_labels) and (not body or body[-1].get("op") not in ("return", "jump")):
                following[name] = top_labels[index + 1]["name"]
    selected = []
    for name in roots:
        if name not in owners:
            raise ValueError(f"no existe la etiqueta {name}")
        if owners[name] not in selected:
            selected.append(owners[name])
    for name in selected:
        targets = [node.get("label") for node in walk([labels[name]]) if node.get("op") in ("call", "jump")]
        targets += [following[name]] if name in following else []
        for target in targets:
            if target is None:
                continue
            if target not in owners:
                raise ValueError(f"etiqueta sin resolver desde {name}: {target}")
            if owners[target] not in selected:
                selected.append(owners[target])
    destinations = {name: (selected.index(owner), None) for name, owner in owners.items() if owner in selected}
    call_graph = {name: {owners[node["label"]] for node in walk([labels[name]])
                         if node.get("op") == "call" and node.get("label") in owners}
                  for name in selected}
    for name in selected:
        if not labels[name].get("parameters"):
            continue
        pending = list(call_graph[name])
        visited = set()
        while pending:
            target = pending.pop()
            if target == name:
                raise ValueError(f"recursion con parametros sin soporte: {name}")
            if target not in visited:
                visited.add(target)
                pending.extend(call_graph.get(target, ()))
    variables = {}
    speakers = guion.hablantes(script)
    chapters = []
    for index, name in enumerate(selected):
        chapter = Capitulo(name, speakers, script, variables, destinations, index, text_layout)
        chapter.etiquetas[name] = 0
        chapter.compilar(labels[name].get("body") or [])
        if name in following:
            chapter._salto({"op": "jump", "label": following[name]})
        for label, offset in chapter.etiquetas.items():
            destinations[label] = (index, offset)
        chapters.append(chapter)
    result = []
    text_base = 0
    limits = formatos.engine_limits()
    for index, chapter in enumerate(chapters):
        code = chapter.terminar()
        vnb = formatos.vnb(code, len(chapter.textos), index, text_base, chapter.animations)
        texts = formatos.bloque_texto(chapter.textos)
        formatos.check_chapter_size(f"{index:02d} ({chapter.nombre})", vnb, texts, limits)
        result.append((vnb, texts, chapter))
        text_base += len(chapter.textos)
    return Program(result, variables, destinations, speakers)
