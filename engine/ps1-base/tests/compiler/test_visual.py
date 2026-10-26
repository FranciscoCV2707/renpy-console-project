import struct

import pytest

from vncompiler.compilar import Capitulo


def test_resolved_visuals_use_existing_vnb1_instructions():
    chapter = Capitulo("test", {}, {"script": {}})
    chapter.compilar([{"op": "ps1_scene", "image": 1},
                      {"op": "ps1_show", "tag": 2, "image": 3, "position": 1},
                      {"op": "ps1_hide", "tag": 2}])
    assert chapter.codigo == (b"\x10" + struct.pack("<HH", 1, 0)
                              + b"\x11" + struct.pack("<BHBbBH", 2, 3, 1, -128, 0, 0)
                              + b"\x12\x02")
    assert chapter.reporte == {"SCENE": 1, "SHOW": 1, "HIDE": 1}


@pytest.mark.parametrize("node", [{"op": "ps1_show", "image": 0, "tag": 1},
                                     {"op": "ps1_show", "image": 1, "tag": 256},
                                     {"op": "ps1_scene", "image": -1},
                                     {"op": "ps1_hide", "tag": True}])
def test_visual_fields_are_validated(node):
    chapter = Capitulo("test", {}, {"script": {}})
    with pytest.raises(ValueError, match="fuera de rango"):
        chapter.compilar([node])
