"""Run the Windows CMS slice over HTTP, or write a sample theme for the builder."""

import argparse
from contextlib import contextmanager
import io
import json
import os
from pathlib import Path
from queue import Queue
import subprocess
from tempfile import TemporaryDirectory
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from zipfile import ZIP_DEFLATED, ZipFile


def sample_theme(descriptor="block.json"):
    archive = io.BytesIO()
    with ZipFile(archive, "w", ZIP_DEFLATED) as theme:
        theme.writestr(descriptor, json.dumps({
            "id": "sample/banner",
            "fields": {"title": "Tiêu đề", "note": "Mô tả"},
        }))
        theme.writestr("block.html", "<article><h2>{{ values.title }}</h2><p>{{ values.note }}</p></article>")
    return archive.getvalue()


@contextmanager
def running(binary, database):
    env = dict(os.environ, OPENDASH_PORT="0", OPENDASH_DB_PATH=str(database))
    with subprocess.Popen(
        [str(binary)], env=env, stdout=subprocess.PIPE, text=True, encoding="utf-8"
    ) as process:
        output = Queue()
        Thread(target=lambda: output.put(process.stdout.readline()), daemon=True).start()
        try:
            line = output.get(timeout=20).strip()
            assert line.startswith("OpenDash: http://127.0.0.1:") and line.endswith("/builder"), line
            yield line.removeprefix("OpenDash: ").removesuffix("/builder")
        finally:
            process.terminate()


def request(base, path, data=None, content_type=None):
    headers = {"Content-Type": content_type} if content_type else {}
    try:
        with urlopen(Request(base + path, data=data, headers=headers), timeout=5) as response:
            return response.status, response.read().decode("utf-8")
    except HTTPError as error:
        with error:
            return error.code, error.read().decode("utf-8")


def verify(binary):
    block = {"type": "sample/banner", "values": {"title": "Dự án A < B", "note": "{{ 7 * 7 }}"}}
    body = json.dumps(block, ensure_ascii=False).encode()
    with TemporaryDirectory(prefix="opendash-smoke-") as folder:
        database = Path(folder) / "cms.sqlite"
        with running(binary, database) as base:
            assert request(base, "/builder")[0] == 200
            assert json.loads(request(base, "/registry")[1]) == {}
            assert request(base, "/theme", sample_theme("../block.json"), "application/zip")[0] == 400
            assert request(base, "/theme", sample_theme(), "application/zip")[0] == 201
            assert json.loads(request(base, "/registry")[1]) == {
                "sample/banner": {"note": "Mô tả", "title": "Tiêu đề"}
            }
            status, preview = request(base, "/preview", body, "application/json")
            assert status == 200 and "Dự án A &lt; B" in preview and "{{ 7 * 7 }}" in preview
            assert request(base, "/")[1] == "<p>Chưa lưu block.</p>"
            assert request(base, "/save", body, "application/json") == (200, preview)
            assert request(base, "/") == (200, preview)
            assert request(base, "/save", b'{"type":"sample/banner","values":{}}', "application/json")[0] == 400
            assert request(base, "/theme", sample_theme(), "application/zip")[0] == 409
            assert request(base, "/") == (200, preview)
        with running(binary, database) as base:
            assert json.loads(request(base, "/page")[1]) == block
            assert request(base, "/") == (200, preview)
    print("PASS: ZIP install, preview isolation, save, rejected inputs, and SQLite persistence after restart")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=Path("target/debug/opendash.exe"))
    parser.add_argument("--theme", type=Path, help="Write a sample theme ZIP instead of running the check")
    args = parser.parse_args()
    if args.theme:
        args.theme.write_bytes(sample_theme())
        print(args.theme.resolve())
    else:
        verify(args.binary.resolve())
