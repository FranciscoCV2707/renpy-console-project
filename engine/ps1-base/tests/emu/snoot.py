"""Pruebas en emulador de Snoot con el motor compartido (docs/diseno.md, sección 6).

Arma discos de Snoot con un motor y los datos de snoot-ps1 (que solo se leen), corre guiones de
botones en PCSX-Redux sin interfaz y compara las capturas píxel a píxel con las de referencia.

    python tests/emu/snoot.py record [--only NOMBRE ...]   referencia: el motor en REF_COMMIT
    python tests/emu/snoot.py check  [--only NOMBRE ...]   el motor de este repo contra la referencia

REF_COMMIT es la copia sin cambios del motor de snoot-ps1 v1.0 (compila byte a byte igual). Se arma en
un worktree de git dentro de build/emu/. Nada se escribe en snoot-ps1: las herramientas de allá se
importan sin dejar caché de Python, y sus carpetas de trabajo se redirigen a build/emu/.

El ejecutable se rellena hasta un tamaño fijo en el disco de prueba: así los archivos de datos quedan
en los mismos sectores aunque el motor cambie de tamaño, y los tiempos de carga son los mismos. El
cargador de la PS1 lee solo lo que dice la cabecera del ejecutable.
"""
import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
SNOOT = Path(r"E:\Dev\snoot-ps1")
sys.path.insert(0, str(SNOOT))

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from tools.engine import build_game as bg  # noqa: E402
from tools.engine import emutest as et  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
BUILD = REPO / "build" / "emu"
REF_COMMIT = "f770b2e"
EXE_SIZE = 256 * 1024

# Filas del menú de desarrollo (L1+R1+Select en el título): 4 = capítulo 4 (chat), 30 = 14D (ruta 4, créditos),
# 29 = 13D (teclado). Estados del motor (main.c): 16 SCROLL, 17 CREDITS, 18 INPUT.
DEV = "60 press L1; 60 press R1; 60 press SELECT; 120 shot dev"


def dev_row(row, start=130, autoplay=True):
    """Elige la fila del menú de desarrollo y juega en automático, o (autoplay=False) solo la abre."""
    steps = [f"{start + 10 * i} press DOWN" for i in range(row)] + [f"{start + 10 * row + 20} press CROSS"]
    if autoplay:
        steps.append(f"{start + 10 * row + 80} autoplay")
    return "; ".join(steps)


def skipping(row, until, every=60):
    """Abre la fila y avanza con el salto de texto (R1; en el menú de desarrollo salta también lo no leído). Cada
    `every` cuadros: X (elige en una decisión, o detiene el salto) y enseguida R1 (vuelve a saltar). Una pantalla
    especial detiene el salto y se queda abierta: X no la cierra mientras no se recorra, R1 es suyo."""
    start = 130 + 10 * row + 80
    steps = [dev_row(row, autoplay=False), f"{start} press R1"]
    for frame in range(start + every, until, every):
        steps += [f"{frame} press CROSS", f"{frame + 10} press R1"]
    return "; ".join(steps)


SCENARIOS = {
    "titulo": {"steps": "90 shot titulo; 100 quit"},
    "menus": {"steps": "60 press DOWN; 70 press CROSS; 130 shot continuar; 140 press CROSS; 170 press DOWN; "
                       "180 press CROSS; 240 shot extras; 250 press CROSS; 280 press DOWN; 290 press CROSS; "
                       "380 shot galeria; 390 press CIRCLE; 430 press DOWN; 440 press CROSS; 500 shot opciones; "
                       "510 press LEFT; 540 shot opciones_volumen; 550 press CIRCLE; 600 shot titulo_vuelta; 610 quit"},
    "partida": {"steps": "60 press CROSS; 400 shot inicio; 460 press CROSS; 560 shot linea2; 620 press CROSS; "
                         "720 shot linea3; 780 press START; 840 shot pausa; 850 press DOWN; 860 press DOWN; "
                         "870 press CROSS; 930 shot ranuras; 940 press CROSS; 1100 shot guardado; 1110 press CIRCLE; "
                         "1160 shot tras_guardar; 1200 quit"},
    "cargar": {"steps": "60 press CROSS; 120 shot ranuras_cargar; 130 press CROSS; 450 shot cargada; "
                        "460 quit", "card_from": "partida"},
    "chat": {"steps": f"{DEV}; {skipping(4, 60 * 60 * 8)}", "triggers": "state=16:chat:30; state=16:chat_tarde:300",
             "max_frames": 60 * 60 * 8},
    "teclado": {"steps": f"{DEV}; {dev_row(29)}", "triggers": "state=18:teclado:60", "max_frames": 60 * 60 * 40},
    "creditos": {"steps": f"{DEV}; {skipping(30, 60 * 60 * 15)}",
                 "triggers": "state=17:creditos:60; state=17:creditos_tarde:600", "max_frames": 60 * 60 * 15},
}


def run(args, **kw):
    subprocess.run([str(a) for a in args], check=True, **kw)


def engine_dir(kind):
    """El motor de este repo, o la referencia en un worktree (se crea la primera vez)."""
    if kind == "cur":
        return REPO
    ref = BUILD / "ref-engine"
    if not ref.exists():
        BUILD.mkdir(parents=True, exist_ok=True)
        run(["git", "worktree", "add", "--detach", ref, REF_COMMIT], cwd=REPO, capture_output=True)
    return ref


class PaddedCopy:
    """Reemplaza a shutil dentro de build_game: copia el ejecutable rellenándolo hasta EXE_SIZE."""

    @staticmethod
    def copy(src, dst):
        data = Path(src).read_bytes()
        if len(data) > EXE_SIZE:
            raise SystemExit(f"el ejecutable pasa de {EXE_SIZE} bytes: subir EXE_SIZE")
        Path(dst).write_bytes(data + bytes(EXE_SIZE - len(data)))


def build_disc(engine, autotest, work):
    work.mkdir(parents=True, exist_ok=True)
    bg.WORK, bg.ENGINE, bg.shutil = work, engine, PaddedCopy
    bg.XML = bg.XML.replace('source="../data/MUSIC.XA"', f'source="{(bg.DATA / "MUSIC.XA").as_posix()}"')
    test = work / "AUTOTEST.SRC"
    test.write_bytes(autotest)
    argv = sys.argv
    sys.argv = ["build_game", "--autotest", str(test)]
    try:
        bg.main()
    finally:
        sys.argv = argv
    return work / "snoot_game.cue"


CAMERA_SAMPLES = range(1500, 9000, 1500)
CAMERA = {"steps": "60 press CROSS; " + "; ".join(f"{f} press CROSS" for f in range(150, 9500, 90)) + "; 10000 quit",
          "max_frames": 60 * 60 * 6,
          "pokes": [p for s in CAMERA_SAMPLES for p in
                    ((s, (256, 0, 0), f"cam{s}_normal"), (s + 100, (512, 0, 0), f"cam{s}_zoom2"),
                     (s + 200, (128, 10, 5), f"cam{s}_zoom05"))]}


def poke_lua(sym, pokes):
    """Trozo de Lua para el modo camara: en cada `frame` escribe la camara (zoom 1/256, x e y en pixeles de la
    vista) y 30 cuadros despues toma la captura, cuando el motor ya dibujo el encuadre nuevo."""
    out = ["  if CAM_T == nil and u32(state_addr) == 1 then CAM_T = frames end\n"]
    for frame, (zoom, x, y), name in pokes:
        writes = "; ".join(f"ffi.cast('uint32_t*', mem + {sym[var]})[0] = {val}" for var, val in
                           (("cam_z", zoom), ("cam_z1", zoom), ("cam_x", x), ("cam_x1", x), ("cam_y", y),
                            ("cam_y1", y), ("cam_len", 0)))
        out.append(f"  if CAM_T and frames == CAM_T + {frame} then {writes} end\n"
                   f"  if CAM_T and frames == CAM_T + {frame + 30} then take('{name}') end\n")
    return "".join(out)


def play(name, scenario, kind):
    engine = engine_dir(kind)
    out = BUILD / kind / name
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    if scenario.get("card_from"):
        card = BUILD / kind / scenario["card_from"] / "card1.mcd"
        if not card.exists():
            raise SystemExit(f"{name} usa la memory card de {scenario['card_from']}: correr ese escenario antes")
        shutil.copy(card, out / "card1.mcd")
    steps = et.parse_steps(scenario["steps"])
    cue = build_disc(engine, et.autotest_bin(steps), BUILD / kind / "disc")
    et.ELF = engine / "build" / "snoot.elf"
    sym = et.symbols()
    names = ", ".join(f"'{arg}'" for _, action, arg in steps if action == "shot")
    last = max(f for f, _, _ in steps)
    lua = out / "emutest.lua"
    lua_src = et.LUA % {
        "names": names, "outdir": out.as_posix(), "shot": sym["autotest_shot"], "quit": sym["autotest_quit"],
        "state": sym["state"], "vm": sym["vm"], "watch": ", ".join(f"{n} = {sym[n]}" for n in et.WATCH if n in sym),
        "failog": sym.get("res_fail_log", "nil"), "stalllog": sym.get("stall_log", "nil"),
        "synclog": sym.get("res_sync_log", "nil"), "triggers": et.parse_triggers(scenario.get("triggers")),
        "max_frames": scenario.get("max_frames", last + 3000)}
    if scenario.get("pokes"):
        lua_src = lua_src.replace("  frames = frames + 1\n", "  frames = frames + 1\n" + poke_lua(sym, scenario["pokes"]), 1)
    lua.write_text(lua_src, encoding="utf-8")
    args = [et.REDUX, "-no-ui", "-run", "-fastboot", "-bios", et.BIOS, "-iso", cue, "-memcard1", out / "card1.mcd",
            "-exec", f"dofile('{lua.as_posix()}')"]
    # PCSX-Redux no sale tras PCSX.quit(): cuando el guion escribe final.txt se le da un margen y se cierra
    proc = subprocess.Popen([str(a) for a in args], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.monotonic() + scenario.get("timeout", 3600)
    final_at = None
    while proc.poll() is None and time.monotonic() < deadline:
        if final_at is None and (out / "final.txt").exists():
            final_at = time.monotonic()
        if final_at is not None and time.monotonic() - final_at > 30:
            break
        time.sleep(1)
    if proc.poll() is None:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
        proc.wait()
    log = out / "shots.txt"
    for item in (log.read_text(encoding="utf-8").split(";") if log.exists() else []):
        parts = item.split()
        if len(parts) >= 3:
            et.to_png(out / f"{parts[0]}.raw", int(parts[1]), int(parts[2]))
    final = out / "final.txt"
    return sorted(out.glob("*.png")), final.read_text(encoding="utf-8") if final.exists() else ""


def final_state(text):
    """Dónde terminó: estado y posición del guion (los contadores de rendimiento pueden variar)."""
    keep = ("frames", "state", "cap", "pc", "res_fail_read", "res_fail_vram", "res_fail_clut")
    return {k: v for k, v in (w.split("=", 1) for w in text.split() if "=" in w) if k in keep}


def compare(name):
    ref, cur = BUILD / "ref" / name, BUILD / "cur" / name
    problems = []
    ref_shots = {p.name for p in ref.glob("*.png")}
    cur_shots = {p.name for p in cur.glob("*.png")}
    if not ref_shots:
        problems.append("la referencia no tiene capturas")
    if ref_shots != cur_shots:
        problems.append(f"capturas distintas: faltan {sorted(ref_shots - cur_shots)}, sobran {sorted(cur_shots - ref_shots)}")
    for shot in sorted(ref_shots & cur_shots):
        a = np.asarray(Image.open(ref / shot).convert("RGB"))
        b = np.asarray(Image.open(cur / shot).convert("RGB"))
        if a.shape != b.shape or not np.array_equal(a, b):
            diff = int((a != b).any(axis=2).sum()) if a.shape == b.shape else -1
            problems.append(f"{shot}: {diff} píxeles distintos" if diff >= 0 else f"{shot}: otro tamaño")
    fa = final_state((ref / "final.txt").read_text(encoding="utf-8")) if (ref / "final.txt").exists() else {}
    fb = final_state((cur / "final.txt").read_text(encoding="utf-8")) if (cur / "final.txt").exists() else {}
    if fa != fb:
        problems.append(f"terminó distinto: referencia {fa}, ahora {fb}")
    return problems, len(ref_shots)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["record", "check", "camara"])
    ap.add_argument("--only", nargs="*", help="escenarios (por defecto todos)")
    args = ap.parse_args()
    if args.mode == "camara":
        shots, final = play("camara", CAMERA, "cur")
        print(f"camara: {[p.name for p in shots]}; {final.strip()[:120]}")
        return 0
    names = args.only or list(SCENARIOS)
    kind = "ref" if args.mode == "record" else "cur"
    failed = 0
    for name in names:
        shots, final = play(name, SCENARIOS[name], kind)
        print(f"{name}: {len(shots)} capturas; {final.strip()[:160]}")
        if args.mode == "check":
            problems, total = compare(name)
            if problems:
                failed += 1
                print(f"  DISTINTO ({total} capturas de referencia):")
                for p in problems:
                    print("   ", p)
            else:
                print(f"  igual ({total} capturas idénticas)")
    if args.mode == "check":
        print("OK" if not failed else f"{failed} escenarios distintos")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
