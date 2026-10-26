"""Regresión de Snoot PS1 contra la v1.0: corre las pruebas en emulador de vn-engine-ps1 con el motor de ESTE repo.

Carga E:\\Dev\\vn-engine-ps1\\tests\\emu\\snoot.py sin modificarlo, apunta su motor "actual" a este repo y compara
contra una copia de las capturas de referencia que vn-engine-ps1 ya grabó (build/emu/ref, motor v1.0). Necesita el
Python de snoot-ps1 (numpy, Pillow) y que build/ esté compilado con `cmake --preset default`.

    E:\\Dev\\snoot-ps1\\.venv\\Scripts\\python.exe tests\\emu\\snoot_check.py [--only titulo menus ...]
"""
import importlib.util
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
VN_ENGINE = Path(r"E:\Dev\vn-engine-ps1")
REF_CAPTURES = VN_ENGINE / "build" / "emu" / "ref"

spec = importlib.util.spec_from_file_location("vn_snoot", VN_ENGINE / "tests" / "emu" / "snoot.py")
snoot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snoot)
snoot.REPO = REPO
snoot.BUILD = REPO / "build" / "emu"

if __name__ == "__main__":
    if not REF_CAPTURES.is_dir():
        raise SystemExit(f"faltan las capturas de referencia en {REF_CAPTURES} (grabarlas en vn-engine-ps1 con record)")
    ref = snoot.BUILD / "ref"
    if not ref.exists():
        shutil.copytree(REF_CAPTURES, ref)
    sys.argv = [sys.argv[0], "check", *sys.argv[1:]]
    sys.exit(snoot.main())
