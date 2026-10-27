from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from platforms.ds.convert_bg import convert as convert_ds_background
from tools.demake.ds_pack import convert_background, pack_game
from tools.demake.ima_adpcm import decode, encode
from tools.demake.lz77 import bios_lz77_decompress


class TestDsPack(unittest.TestCase):
    def test_ima_adpcm_round_trip_sine_has_bounded_error(self) -> None:
        original = [round(10000 * math.sin(2 * math.pi * index / 256)) for index in range(1000)]
        restored = decode(encode(original), len(original))
        self.assertEqual(len(restored), len(original))
        self.assertLess(max(abs(left - right) for left, right in zip(original, restored)), 1000)

    def test_background_matches_ds_sample_converter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "sample.png"
            image = Image.new("RGB", (83, 61))
            image.putdata(
                [((index * 17) % 256, (index * 31) % 256, (index * 47) % 256)
                 for index in range(image.width * image.height)]
            )
            image.save(source)
            packed = convert_background(source)
            self.assertEqual(bios_lz77_decompress(packed), convert_ds_background(source))

    def test_manifest_is_identical_across_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            game = root / "game"
            (game / "images" / "backgrounds").mkdir(parents=True)
            (game / "tl" / "es").mkdir(parents=True)
            Image.new("RGB", (32, 24), (60, 120, 180)).save(
                game / "images" / "backgrounds" / "room.png"
            )
            (game / "tl" / "es" / "scene.rpy").write_text(
                'translate es scene_1234:\n    "Hola, mundo"\n', encoding="utf-8"
            )
            first = pack_game(game, root / "one")
            second = pack_game(game, root / "two")
            self.assertEqual((root / "one" / "manifest.json").read_bytes(),
                             (root / "two" / "manifest.json").read_bytes())
            self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
