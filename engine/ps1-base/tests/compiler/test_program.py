import os
import shutil
import struct
import subprocess
from pathlib import Path

import pytest

from vncompiler import formatos
from vncompiler.guion import hablantes, speaker_table
from vncompiler.programa import compile_program
from vncompiler.simulador import simulate

ROOT = Path(__file__).resolve().parents[2]


def label(name, *body, **options):
    return {"op": "label", "name": name, "body": list(body), **options}


def say(text, **options):
    return {"op": "say", "who": None, "text": text, **options}


def assign(name, value, **options):
    return {"op": "set", "var": name, "value": value, **options}


def script(*labels):
    return {"characters": {}, "script": {f"{index}.rpy": [node] for index, node in enumerate(labels)}}


@pytest.fixture(scope="session")
def host(tmp_path_factory):
    gcc = shutil.which("gcc") or next((str(path) for path in [Path(r"C:\msys64\ucrt64\bin\gcc.exe"),
                                                             Path(r"C:\msys64\usr\bin\gcc.exe")] if path.exists()), None)
    if not gcc:
        pytest.fail("se requiere GCC nativo para contrastar el compilador con core/vm.c")
    executable = tmp_path_factory.mktemp("host") / "vm_host.exe"
    environment = {**os.environ, "PATH": str(Path(gcc).parent) + os.pathsep + os.environ["PATH"]}
    subprocess.run([gcc, "-std=c99", "-Wall", "-Wextra", "-Werror", "-I", str(ROOT / "core"),
                    str(ROOT / "tests/compiler/vm_host.c"), str(ROOT / "core/vm.c"), "-o", str(executable)],
                   check=True, capture_output=True, text=True, env=environment)
    return executable, environment


def compare(host, tmp_path, program, choices=(), start=0):
    program.write(tmp_path)
    chapters = {index: data for index, (data, _, _) in enumerate(program.chapters)}
    expected = simulate(chapters, start=start, choices=choices)
    executable, environment = host
    actual = subprocess.run([str(executable), str(tmp_path), str(start), ",".join(map(str, choices))],
                            capture_output=True, text=True, check=True, env=environment)
    assert actual.stdout.splitlines() == expected
    return expected


def test_nested_cross_chapter_calls_return_values_and_global_variables(host, tmp_path):
    source = script(
        label("main", assign("score", {"const": 3}), {"op": "call", "label": "second"},
              say("after"), {"op": "return"}),
        label("second", assign("other", {"const": 5}), {"op": "call", "label": "third"},
              assign("score", {"var": "_return"}, aug="+"), {"op": "return"}),
        label("third", say("original"), {"op": "return", "value": {"const": 7}}))
    program = compile_program(source, ["main"])
    trace = compare(host, tmp_path, program)
    assert [line for line in trace if line.startswith("SAY")] == ["SAY 2 0 1 0", "SAY 0 0 0 0"]
    assert trace[-1].split()[1].split(",")[program.variables["score"]] == "10"
    assert [struct.unpack_from("<H", data, 4)[0] for data, _, _ in program.chapters] == [0, 1, 2]


@pytest.mark.parametrize("enabled,choice,expected", [(0, 0, "always"), (1, 0, "conditional"), (1, 1, "always")])
def test_conditional_menus_and_compound_conditions(host, tmp_path, enabled, choice, expected):
    condition = {"and": [{"var": "enabled"}, {"not": {"const": False}},
                          {"cmp": ["<", "<="], "l": {"const": 0}, "r": [{"const": 1}, {"const": 2}]}]}
    source = script(label("main", assign("enabled", {"const": enabled}),
                          {"op": "menu", "choices": [
                              {"text": "conditional", "if": condition, "body": [say("conditional")]},
                              {"text": "always", "body": [say("always")]}]}, {"op": "return"}))
    program = compile_program(source, ["main"])
    trace = compare(host, tmp_path, program, [choice])
    index = program.chapters[0][2].textos.index(expected.encode(), 2)
    assert f"SAY 0 {index} {index} 0" in trace
    assert f"MENU {2 if enabled else 1} " in next(line for line in trace if line.startswith("MENU"))


def test_empty_conditional_menu_falls_through(host, tmp_path):
    program = compile_program(script(label("main", {"op": "menu", "choices": [
        {"text": "hidden", "if": {"const": False}, "body": [say("wrong")]}]}, say("after"))), ["main"])
    trace = compare(host, tmp_path, program)
    assert not any(line.startswith("MENU") for line in trace)
    assert sum(line.startswith("SAY") for line in trace) == 1


def test_missing_translation_keeps_original_and_nested_labels_link(host, tmp_path):
    source = script(label("main", {"op": "jump", "label": "inside"}, say("unreachable"),
                          label("inside", say("English fallback"), {"op": "return"})))
    program = compile_program(source, ["main"])
    compare(host, tmp_path, program)
    assert b"English fallback\x00" in program.chapters[0][1]
    assert program.destinations["inside"][1] > 0


def test_fallthrough_between_top_level_labels(host, tmp_path):
    source = {"characters": {}, "script": {"one.rpy": [label("main", say("one")),
                                                               label("next", say("two"), {"op": "return"})]}}
    trace = compare(host, tmp_path, compile_program(source, ["main"]))
    assert sum(line.startswith("SAY") for line in trace) == 2


def test_call_parameters_defaults_and_keywords(host, tmp_path):
    source = script(label("main", {"op": "call", "label": "helper"},
                          {"op": "call", "label": "helper", "args": [
                              {"kind": "keyword", "name": "amount", "value": {"const": 8}}]}),
                    label("helper", assign("score", {"var": "amount"}, aug="+"), {"op": "return"},
                          parameters=[{"name": "amount", "default": {"const": 2}}]))
    program = compile_program(source, ["main"])
    trace = compare(host, tmp_path, program)
    assert trace[-1].split()[1].split(",")[program.variables["score"]] == "10"


def test_unsupported_conditions_stop_instead_of_selecting_else(host, tmp_path):
    source = script(label("main", {"op": "if", "branches": [
        {"if": {"call": "unknown", "args": []}, "body": [say("true")]},
        {"if": None, "body": [say("wrong else")]}]}))
    program = compile_program(source, ["main"])
    with pytest.raises(ValueError, match="HALT"):
        simulate({0: program.chapters[0][0]})
    program.write(tmp_path)
    executable, environment = host
    result = subprocess.run([str(executable), str(tmp_path), "0"], capture_output=True, text=True, env=environment)
    assert result.returncode == 4 and "HALT" in result.stderr
    assert program.chapters[0][2].diagnostics


def test_unresolved_labels_fail_compilation():
    with pytest.raises(ValueError, match="sin resolver"):
        compile_program(script(label("main", {"op": "jump", "label": "missing"})), ["main"])


def test_speaker_ids_match_names_and_narrator_aliases():
    source = {"characters": {"base": {"name": ""}, "I": {"name": "Inco"},
                              "narrator": {"name": ""}, "pair": {"name": "{image=Name} & Inco"}},
              "images": {"Name": {"value": {"tree": {"call": "Text", "args": [{"const": "Olivia"}]}}}}}
    assert hablantes(source) == {"base": 0, "I": 1, "narrator": 0, "pair": 2}
    assert [row["name"] for row in speaker_table(source)] == ["", "Inco", "Olivia & Inco"]


def test_recursive_parameters_are_rejected_instead_of_overwritten():
    source = script(label("first", {"op": "call", "label": "second"},
                          parameters=[{"name": "amount", "default": {"const": 1}}]),
                    label("second", {"op": "call", "label": "first"}))
    with pytest.raises(ValueError, match="recursion con parametros"):
        compile_program(source, ["first"])


def test_external_jump_does_not_add_a_return_frame(host, tmp_path):
    source = script(label("main", {"op": "call", "label": "first"}, say("back")),
                    label("first", {"op": "jump", "label": "second"}, say("wrong")),
                    label("second", say("second"), {"op": "return"}))
    trace = compare(host, tmp_path, compile_program(source, ["main"]))
    assert sum(line.startswith("SAY") for line in trace) == 2


def test_signed_arithmetic_matches_vm(host, tmp_path):
    source = script(label("main", assign("value", {"const": 32767}),
                          assign("value", {"const": 1}, aug="+"),
                          assign("result", {"neg": {"const": 7}}),
                          assign("result", {"bin": "*", "l": {"var": "result"}, "r": {"const": 3}})))
    program = compile_program(source, ["main"])
    trace = compare(host, tmp_path, program)
    values = trace[-1].split()[1].split(",")
    assert values[program.variables["value"]] == "-32768"
    assert values[program.variables["result"]] == "-21"


@pytest.mark.parametrize("code,error", [(b"\x01", "truncada"), (b"\x40\x00\x01", "menu invalido"),
    (b"\x19\x00\x00\x01", "menu de imagenes invalido"), (b"\x1a\x20", "telefono invalido"),
    (b"\x50\x40\x00\x00", "variable fuera de rango"), (b"\x54\xff", "operador invalido"),
    (b"\x40\x00\x01\x01\x00\x00\x00\x00\x00", "texto de menu fuera de rango")])
def test_vm_rejects_malformed_bytecode(host, tmp_path, code, error):
    (tmp_path / "C00.VNB").write_bytes(formatos.vnb(code, 1))
    executable, environment = host
    result = subprocess.run([str(executable), str(tmp_path), "0"], capture_output=True, text=True, env=environment)
    assert result.returncode == 4 and error in result.stderr
