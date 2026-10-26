import struct
import pytest
from vncompiler.audio import encode_audio
from vncompiler.programa import compile_program
from vncompiler.simulador import simulate


@pytest.mark.parametrize("node,opcode,payload", [
    ({"action": "music_play", "id": 7, "fade": 30}, 0x20, b"\x07\x00\x1e\x00"),
    ({"action": "music_queue", "id": 8}, 0x27, b"\x08\x00"),
    ({"action": "ambient_play", "id": 12, "slot": 3, "fade": 20}, 0x22, b"\x03\x0c\x00\x14"),
    ({"action": "volume", "channel": 0, "volume": 128}, 0x26, b"\x00\x80\x00"),
])
def test_resolved_audio_matches_existing_vm_layout(node, opcode, payload):
    assert encode_audio(node)[:2] == (opcode, payload)
    script = {"script": {"audio.rpy": [{"op": "label", "name": "start", "body": [
        {"op": "ps1_audio", **node}, {"op": "say", "id": "line", "text": "Hola"}, {"op": "return"}]}]}}
    program = compile_program(script, ["start"])
    vnb = program.chapters[0][0]
    assert vnb[32:33 + len(payload)] == bytes([opcode]) + payload
    assert simulate({0: vnb})[0].startswith("SAY")


@pytest.mark.parametrize("node", [
    {"action": "missing"}, {"action": "music_play", "id": 256},
    {"action": "ambient_play", "slot": 4}, {"action": "volume", "volume": -1},
    {"action": "volume", "channel": True}, {"action": "music_stop", "fade": 1.5},
])
def test_audio_rejects_invalid_parameters(node):
    with pytest.raises(ValueError):
        encode_audio(node)
