"""Compila build/gba/snoot.gba con devkitARM dentro de Docker (T-710)."""
from __future__ import annotations

import argparse
import shutil
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMAGE = "devkitpro/devkitarm@sha256:116afba8df8453961de2936ffab20dd441edf4d682856c1ec8b0e53d7ed0bbf5"
SRC = Path(__file__).resolve().parent
WORK = ROOT / "build" / "gba" / "work"
OUT = ROOT / "build" / "gba" / "snoot.gba"
DISC = ROOT / "build" / "ctl" / "ps1" / "disc"

IGNORE_EXTENSIONS = {".cue", ".iso", ".exe", ".cnf", ".spu"}
IGNORE_NAMES = {"snoot_game.bin", "autotest.bin"}


def make_gbfs(files: list[tuple[str, bytes]]) -> bytes:
    """Empaqueta una lista de (nombre, contenido) en formato GBFS v1."""
    magic = b"PinEightGBFS\r\n\x1a\n"
    descs_count = len(files)
    dir_ofs = 32
    dir_size = descs_count * 32
    payload_ofs = dir_ofs + dir_size

    entries: list[bytes] = []
    payloads: list[bytes] = []
    cur_ofs = payload_ofs

    for name, data in files:
        cur_ofs = (cur_ofs + 3) & ~3
        name_bytes = name.encode("ascii", errors="replace")[:23]
        name_padded = name_bytes.ljust(24, b"\x00")
        entry = struct.pack("<24sII", name_padded, len(data), cur_ofs)
        entries.append(entry)

        padding = b"\x00" * (cur_ofs - (payload_ofs + sum(len(p) for p in payloads)))
        payloads.append(padding + data)
        cur_ofs += len(data)

    total_len = (cur_ofs + 255) & ~255
    padding_end = b"\x00" * (total_len - cur_ofs)
    payloads.append(padding_end)

    header = struct.pack("<16sIHH8s", magic, total_len, dir_ofs, descs_count, b"\x00" * 8)
    return header + b"".join(entries) + b"".join(payloads)


def prepare_work() -> None:
    if WORK.exists():
        for folder in (
            "build",
            "source",
            "engine_core",
            "engine_app",
            "engine_modules",
            "games_snoot",
            "include",
            "generated",
        ):
            target = WORK / folder
            if target.exists():
                shutil.rmtree(target)
    WORK.mkdir(parents=True, exist_ok=True)

    shutil.copytree(SRC / "source", WORK / "source")
    if (SRC / "gba_cart.ld").is_file():
        shutil.copy2(SRC / "gba_cart.ld", WORK / "gba_cart.ld")
    if (SRC / "custom.specs").is_file():
        shutil.copy2(SRC / "custom.specs", WORK / "custom.specs")
    shutil.copytree(ROOT / "engine" / "core", WORK / "engine_core")
    shutil.copytree(ROOT / "engine" / "app", WORK / "engine_app")
    shutil.copytree(ROOT / "engine" / "modules", WORK / "engine_modules")
    shutil.copytree(ROOT / "games" / "snoot", WORK / "games_snoot")

    include_dir = WORK / "include"
    include_dir.mkdir(parents=True, exist_ok=True)
    for header in (ROOT / "engine" / "platform").glob("*.h"):
        shutil.copy2(header, include_dir / header.name)

    generated = WORK / "generated"
    generated.mkdir(parents=True, exist_ok=True)
    (generated / "game_config.h").write_text(
        '#pragma once\n#define VN_SEEN_BYTES 2048\n#define VN_SAVE_TITLE "SNOOT GAME"\n'
        '#define VN_SAVE_PREFIX "BASLUS-99999SNOOT"\n#define VN_SAVE_MAGIC "SNS1"\n',
        encoding="utf-8",
        newline="\n",
    )


def docker_sh(script: str) -> None:
    subprocess.run(
        ["docker", "run", "--rm", "-v", f"{ROOT.as_posix()}:/src", "-w", "/src/build/gba/work", IMAGE, "sh", "-c", script],
        cwd=ROOT,
        check=True,
    )


def build(trace: bool = False, autotest_path: Path | None = None) -> Path:
    if not DISC.is_dir():
        raise FileNotFoundError("faltan los datos del disco PS1; ejecuta primero ctl run --target ps1")

    prepare_work()
    OUT.parent.mkdir(parents=True, exist_ok=True)

    # Lista de fuentes C a compilar
    c_sources = [
        "engine_core/vn_platform.c",
        "engine_core/lz4.c",
        "engine_core/str.c",
        "engine_core/chapter.c",
        "engine_core/scene.c",
        "engine_core/text.c",
        "engine_core/vm.c",
        "engine_app/main.c",
        "engine_modules/credits.c",
        "engine_modules/strips.c",
        "engine_modules/canvas.c",
        "engine_modules/keyboard.c",
        "engine_modules/phone.c",
        "games_snoot/game.c",
        "games_snoot/text.c",
        "games_snoot/specials.c",
        "source/backend_gba.c",
        "source/video.c",
        "source/img.c",
        "source/res.c",
        "source/cd.c",
        "source/input.c",
        "source/save.c",
        "source/audio.c",
        "source/gbfs.c",
    ]

    compile_cmds: list[str] = [". /opt/devkitpro/devkitarm.sh", "mkdir -p build/obj"]
    obj_files: list[str] = []

    trace_flag = "-DVN_TRACE=1" if trace else ""
    includes = (
        "-I/src/build/gba/work/include "
        "-I/src/build/gba/work/source "
        "-I/src/build/gba/work/engine_core "
        "-I/src/build/gba/work/engine_app "
        "-I/src/build/gba/work/engine_modules "
        "-I/src/build/gba/work/games_snoot "
        "-I/src/build/gba/work/generated "
        "-I/opt/devkitpro/libtonc/include"
    )

    cflags = (
        f"-std=c99 -Wall -Wextra -Wno-unused-parameter -pedantic "
        f"-mcpu=arm7tdmi -mthumb -mthumb-interwork -O2 {trace_flag} {includes}"
    )

    for src in c_sources:
        obj_name = src.replace("/", "_").replace(".c", ".o")
        obj_path = f"build/obj/{obj_name}"
        obj_files.append(obj_path)
        compile_cmds.append(f"arm-none-eabi-gcc {cflags} -c {src} -o {obj_path}")

    objs_str = " ".join(obj_files)
    link_cmd = (
        f"arm-none-eabi-gcc -mcpu=arm7tdmi -mthumb -mthumb-interwork "
        f"-specs=/src/build/gba/work/custom.specs "
        f"{objs_str} -L/opt/devkitpro/libtonc/lib -ltonc -o build/snoot.elf && "
        f"arm-none-eabi-objcopy -O binary build/snoot.elf build/snoot.raw"
    )
    compile_cmds.append(link_cmd)

    full_script = " && ".join(compile_cmds)
    docker_sh(full_script)

    # Crear archivo GBFS con los datos del disco
    gbfs_files: list[tuple[str, bytes]] = []
    for item in sorted(DISC.glob("*")):
        if item.is_file():
            if item.suffix.lower() in IGNORE_EXTENSIONS or item.name.lower() in IGNORE_NAMES:
                continue
            gbfs_files.append((item.name.upper(), item.read_bytes()))

    if autotest_path and autotest_path.is_file():
        gbfs_files.append(("AUTOTEST.BIN", autotest_path.read_bytes()))

    gbfs_data = make_gbfs(gbfs_files)

    # Leer snoot.raw, alinear a 256 bytes y concatenar GBFS
    raw_path = WORK / "build" / "snoot.raw"
    raw_data = raw_path.read_bytes()
    pad_len = ((len(raw_data) + 255) & ~255) - len(raw_data)
    combined = raw_data + (b"\x00" * pad_len) + gbfs_data

    OUT.write_bytes(combined)

    # Corregir la cabecera GBA con gbafix
    fix_script = f"/opt/devkitpro/tools/bin/gbafix /src/build/gba/snoot.gba -tSNOOT -c0000 -m00"
    docker_sh(fix_script)

    return OUT


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--autotest-path", type=Path, default=None)
    args = parser.parse_args()
    print(build(args.trace, args.autotest_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
