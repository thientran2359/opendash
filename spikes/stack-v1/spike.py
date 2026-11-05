"""Small local probe of ZIP extension contracts. Run with --serve for the builder demo."""

import argparse
import io
import json
import re
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from minijinja import Environment, TemplateError
import wasmtime

MAX_BYTES = 64 * 1024
TEXT_KEY = re.compile(r"[a-z][a-z0-9_]{0,31}")
BLOCK_ID = re.compile(r"[a-z][a-z0-9-]*/[a-z][a-z0-9-]*")


def unpack(package, names):
    if len(package) > MAX_BYTES:
        raise ValueError("ZIP too large")
    try:
        with ZipFile(io.BytesIO(package)) as archive:
            entries = archive.infolist()
            if len(entries) != len(names) or {entry.filename for entry in entries} != names:
                raise ValueError("Unexpected or duplicate ZIP entries")
            if sum(entry.file_size for entry in entries) > MAX_BYTES:
                raise ValueError("Expanded ZIP too large")
            return {name: archive.read(name) for name in names}
    except (BadZipFile, RuntimeError) as exc:
        raise ValueError("Unreadable ZIP") from exc


class Builder:
    def __init__(self):
        self.registry = {}
        self.saved = None

    def install(self, package):
        files = unpack(package, {"block.json", "block.html"})
        block = json.loads(files["block.json"])
        if not isinstance(block, dict):
            raise ValueError("Invalid block descriptor")
        name, fields = block.get("id"), block.get("fields")
        if not isinstance(name, str) or not BLOCK_ID.fullmatch(name) or name in self.registry:
            raise ValueError("Invalid or duplicate block ID")
        if not isinstance(fields, dict) or not fields or len(fields) > 12:
            raise ValueError("Invalid fields")
        if any(not TEXT_KEY.fullmatch(key) or not isinstance(label, str)
               for key, label in fields.items()):
            raise ValueError("Invalid text field")
        env = Environment()
        env.add_template("block.html", files["block.html"].decode("utf-8"))
        self.registry[name] = (fields, env)

    def descriptors(self):
        return {name: fields for name, (fields, _) in self.registry.items()}

    def render(self, node):
        name, values = node.get("type"), node.get("values")
        if not isinstance(name, str) or name not in self.registry:
            raise ValueError("Unknown block")
        fields, env = self.registry[name]
        if not isinstance(values, dict) or values.keys() != fields.keys():
            raise ValueError("Fields do not match descriptor")
        if any(not isinstance(value, str) or len(value) > 512 for value in values.values()):
            raise ValueError("Invalid text value")
        return env.render_template("block.html", values=values)

    def save(self, node):
        html = self.render(node)
        self.saved = node
        return html

    def public(self):
        return self.render(self.saved) if self.saved is not None else "<p>Chưa lưu block.</p>"


class Plugins:
    def __init__(self):
        config = wasmtime.Config()
        config.consume_fuel = True
        self.engine = wasmtime.Engine(config)
        self.active = None
        self.host_calls = 0

    def install(self, package):
        files = unpack(package, {"plugin.json", "plugin.wasm"})
        manifest = json.loads(files["plugin.json"])
        declared = manifest.get("permissions")
        if not isinstance(declared, list) or any(p != "content.read" for p in declared):
            raise ValueError("Unsupported permission")
        self.active = (declared, wasmtime.Module(self.engine, files["plugin.wasm"]))

    def disable(self):
        self.active = None

    def run(self):
        if self.active is None:
            raise ValueError("Plugin disabled")
        declared, module = self.active
        store = wasmtime.Store(self.engine)
        store.set_limits(memory_size=65536, table_elements=8, instances=1, tables=1, memories=1)
        store.set_fuel(50000)
        linker = wasmtime.Linker(self.engine)

        def read_content():
            self.host_calls += 1
            return 41

        if "content.read" in declared:
            linker.define_func("cms", "read_content", wasmtime.FuncType([], [wasmtime.ValType.i32()]), read_content)
        # No WASI and no generic host bridge. Missing imports fail at instantiation.
        instance = linker.instantiate(store, module)
        return instance.exports(store)["run"](store)


def serve(port):
    builder = Builder()
    page = Path(__file__).with_name("builder.html").read_text(encoding="utf-8")

    class Handler(BaseHTTPRequestHandler):
        def respond(self, payload, content_type="text/html", status=200):
            data = payload.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type + "; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-Content-Type-Options", "nosniff")
            if self.path not in ("/builder", "/registry", "/page"):
                self.send_header("Content-Security-Policy", "sandbox; default-src 'none'")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path == "/builder":
                self.respond(page)
            elif self.path == "/registry":
                self.respond(json.dumps(builder.descriptors()), "application/json")
            elif self.path == "/page":
                self.respond(json.dumps(builder.saved), "application/json")
            elif self.path == "/":
                self.respond(builder.public())
            else:
                self.respond("Not found", "text/plain", 404)

        def do_POST(self):
            try:
                size = int(self.headers.get("Content-Length", 0))
                if not 0 < size <= MAX_BYTES:
                    raise ValueError("Invalid request size")
                body = self.rfile.read(size)
                if self.path == "/theme":
                    builder.install(body)
                    self.respond("Installed", "text/plain", 201)
                elif self.path in ("/preview", "/save"):
                    node = json.loads(body)
                    if not isinstance(node, dict):
                        raise ValueError("Invalid node")
                    render = builder.render if self.path == "/preview" else builder.save
                    self.respond(render(node))
                else:
                    self.respond("Not found", "text/plain", 404)
            except (ValueError, TemplateError) as exc:
                self.respond(str(exc), "text/plain", 400)

    with HTTPServer(("127.0.0.1", port), Handler) as server:
        print(f"Local spike: http://127.0.0.1:{server.server_port}/builder", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", type=int, metavar="PORT", required=True)
    try:
        serve(parser.parse_args().serve)
    except KeyboardInterrupt:
        sys.exit(0)
