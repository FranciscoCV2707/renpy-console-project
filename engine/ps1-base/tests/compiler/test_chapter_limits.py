"""Capitulos grandes (PAKO-14): el compilador rechaza lo que el motor no carga y core/chapter.c los pone en el heap.

Los limites viven en core/vn_limits.h; el compilador los lee de ahi. La parte nativa compila core/chapter.c con GCC
contra un CD de archivos en disco y un malloc contado: capitulos mas grandes que los viejos buffers fijos (48 KiB de
VNB, 80 KiB de texto) cargan, solo queda un bloque vivo y los rechazos no dejan memoria tomada.
"""
import os
import subprocess
from pathlib import Path

import pytest

from vncompiler import formatos
from vncompiler.programa import compile_program

ROOT = Path(__file__).resolve().parents[2]
GCC = Path(r"C:\msys64\ucrt64\bin\gcc.exe")


def script(lines):
    body = [{"op": "say", "id": f"l{index}", "text": f"linea {index} " + "x" * 80} for index in range(lines)]
    return {"script": {"test.rpy": [{"op": "label", "name": "start", "body": body}]}}


def test_limits_come_from_engine_header():
    limits = formatos.engine_limits()
    assert limits["VN_CHAPTER_MAX_BYTES"] == 98304
    assert limits["VN_TEXT_MAX_BYTES"] == 98304
    assert '#include "vn_limits.h"' in (ROOT / "core/chapter.c").read_text(encoding="utf-8")


def test_check_accepts_exact_limit_and_names_chapter_size_and_limit():
    limits = {"VN_CHAPTER_MAX_BYTES": 100, "VN_TEXT_MAX_BYTES": 50}
    formatos.check_chapter_size("06 (ch6)", b"v" * 100, b"t" * 50, limits)
    with pytest.raises(ValueError, match=r"capitulo 06 \(ch6\): VNB de 101 bytes excede el limite del motor de 100"):
        formatos.check_chapter_size("06 (ch6)", b"v" * 101, b"t", limits)
    with pytest.raises(ValueError, match=r"capitulo 18D: texto de 51 bytes excede el limite del motor de 50"):
        formatos.check_chapter_size("18D", b"v", b"t" * 51, limits)


def test_compile_program_fails_on_oversized_chapter(monkeypatch):
    program = compile_program(script(20), ["start"])
    vnb, texts, _ = program.chapters[0]
    monkeypatch.setattr(formatos, "engine_limits",
                        lambda: {"VN_CHAPTER_MAX_BYTES": len(vnb), "VN_TEXT_MAX_BYTES": len(texts) - 1})
    with pytest.raises(ValueError, match=rf"capitulo 00 \(start\): texto de {len(texts)} bytes"):
        compile_program(script(20), ["start"])


def test_real_limits_accept_chapter_bigger_than_old_buffers():
    vnb, texts, _ = compile_program(script(900), ["start"]).chapters[0]
    assert len(texts) > 80 * 1024


HARNESS = r"""
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const char *dir;
static int live, fail_next;
static long last_size;

static FILE *open_data(const char *path)
{
    char name[512];
    snprintf(name, sizeof(name), "%s/%s", dir, path + 6); /* "\\DATA\\" */
    return fopen(name, "rb");
}

int cd_find(const char *path, int *lba, int *size)
{
    FILE *f = open_data(path);
    if (!f)
        return -1;
    fseek(f, 0, SEEK_END);
    *size = (int)ftell(f);
    *lba = 0;
    fclose(f);
    return 0;
}

int cd_read_file(const char *path, void *buf, int buf_bytes)
{
    int lba, size;
    FILE *f;
    if (cd_find(path, &lba, &size) != 0 || (size + 2047) / 2048 * 2048 > buf_bytes)
        return -1;
    f = open_data(path);
    memset(buf, 0xee, buf_bytes);
    fread(buf, 1, size, f);
    fclose(f);
    return size;
}

static void *test_malloc(size_t n)
{
    if (fail_next) {
        fail_next = 0;
        return 0;
    }
    live++;
    last_size = (long)n;
    return malloc(n);
}

static void test_free(void *p)
{
    live--;
    free(p);
}

#define malloc test_malloc
#define free test_free
#include "chapter.c"
#undef malloc
#undef free

int main(int argc, char **argv)
{
    VmChapter ch;
    int rc;
    (void)argc;
    dir = argv[1];
    /* las lineas del arnes llevan "@"; las demas son los avisos de chapter.c */
    rc = chapter_open(1, &ch);
    printf("@big %d %u %u %u %d %ld %s\n", rc, (unsigned)ch.code_size, (unsigned)ch.text_base, ch.text_count, live,
           last_size, chapter_text(1));
    rc = chapter_open(2, &ch);
    printf("@small %d %u %d %s\n", rc, (unsigned)ch.code_size, live, chapter_text(0));
    rc = chapter_open(3, &ch);
    printf("@toobig %d %d\n", rc, live);
    chapter_open(2, &ch);
    fail_next = 1;
    rc = chapter_open(2, &ch);
    printf("@nomem %d %d\n", rc, live);
    rc = chapter_open(9, &ch);
    printf("@missing %d %d\n", rc, live);
    rc = chapter_open(1, &ch);
    printf("@again %d %d %s\n", rc, live, chapter_text(0));
    return 0;
}
"""


@pytest.mark.skipif(not GCC.exists(), reason="sin GCC nativo de MSYS2")
def test_native_loader_puts_big_chapters_on_heap(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    big_texts = [b"uno " + b"a" * 40000, b"dos " + b"b" * 30000]
    (data / "C01.VNB").write_bytes(formatos.vnb(b"\x00" * 60000, len(big_texts), 1, 5))
    (data / "T01.TXT").write_bytes(formatos.bloque_texto(big_texts))
    (data / "C02.VNB").write_bytes(formatos.vnb(b"\x00" * 10, 1, 2, 7))
    (data / "T02.TXT").write_bytes(formatos.bloque_texto([b"hola"]))
    (data / "C03.VNB").write_bytes(formatos.vnb(b"\x00" * 98304, 1, 3, 8))
    (data / "T03.TXT").write_bytes(formatos.bloque_texto([b"no"]))
    source = tmp_path / "harness.c"
    source.write_text(HARNESS, encoding="utf-8")
    exe = tmp_path / "harness.exe"
    env = {**os.environ, "PATH": str(GCC.parent) + os.pathsep + os.environ["PATH"]}
    subprocess.run([str(GCC), "-std=c99", "-Wall", "-Wextra", "-Werror", "-Wno-unused-result",
                    "-I", str(ROOT / "core"), str(source), "-o", str(exe)], check=True, env=env)
    stdout = subprocess.run([str(exe), str(data)], check=True, env=env, capture_output=True, text=True).stdout
    out = [line[1:] for line in stdout.splitlines() if line.startswith("@")]
    vnb_bytes = (60000 + 32 + 2047) // 2048 * 2048
    text_bytes = (len(formatos.bloque_texto(big_texts)) + 2047) // 2048 * 2048
    big = out[0].split(" ", 7)
    assert big[:7] == ["big", "0", "60000", "5", "2", "1", str(vnb_bytes + text_bytes)]
    assert big[7] == "dos " + "b" * 30000
    assert out[1] == "small 0 10 1 hola"
    assert out[2] == "toobig -1 0"
    assert out[3] == "nomem -1 0"
    assert out[4] == "missing -1 0"
    assert out[5] == "again 0 1 uno " + "a" * 40000
    assert "capitulo 3: VNB 98336 / texto 9 bytes fuera de los limites 98304 / 98304" in stdout
    assert "capitulo 2: sin heap para 4096 bytes" in stdout
