import pytest

from vncompiler.programa import compile_program


def test_resolved_special_uses_existing_opcode():
    script = {"script": {"test": [{"op": "label", "name": "start", "body": [
        {"op": "ps1_special", "special": 200}, {"op": "return"}]}]}}
    program = compile_program(script, ["start"])
    assert program.chapters[0][2].codigo[:2] == bytes((0x31, 200))


@pytest.mark.parametrize("special", [-1, 256, True, "200"])
def test_invalid_special_is_rejected(special):
    script = {"script": {"test": [{"op": "label", "name": "start", "body": [
        {"op": "ps1_special", "special": special}]}]}}
    with pytest.raises(ValueError, match="SPECIAL"):
        compile_program(script, ["start"])
