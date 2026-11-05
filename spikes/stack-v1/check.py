import io
import json
import sys
import unittest
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import wasmtime

from spike import Builder, Plugins


def zip_bytes(files):
    buffer = io.BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


THEME = zip_bytes({
    "block.json": json.dumps({"id": "sample/banner", "fields": {"title": "Tiêu đề", "note": "Mô tả"}}),
    "block.html": '<article><h2>{{ values.title }}</h2><p>{{ values.note }}</p></article>',
})
READ = """(module (import "cms" "read_content" (func $read (result i32)))
    (func (export "run") (result i32) (i32.add (call $read) (i32.const 1))))"""
LOOP = """(module (func (export "run") (loop $again (br $again))))"""
WASI = """(module (import "wasi_snapshot_preview1" "fd_close" (func $close (param i32) (result i32)))
    (func (export "run") (result i32) (call $close (i32.const 0))))"""


def plugin_bytes(module, permissions=()):
    return zip_bytes({
        "plugin.json": json.dumps({"permissions": list(permissions)}),
        "plugin.wasm": module,
    })


def plugin(wat, permissions=()):
    return plugin_bytes(wasmtime.wat2wasm(wat), permissions)


class ExtensionChecks(unittest.TestCase):
    def test_theme_zip_supplies_schema_preview_and_public_render(self):
        builder = Builder()
        self.assertEqual(builder.descriptors(), {})
        builder.install(THEME)
        self.assertEqual(set(builder.descriptors()["sample/banner"]), {"title", "note"})
        builder.save({"type": "sample/banner", "values": {"title": "Old", "note": ""}})
        node = {"type": "sample/banner", "values": {"title": "A < B", "note": "{{ 7 * 7 }}"}}
        preview = builder.render(node)
        self.assertIn("A &lt; B", preview)
        self.assertIn("{{ 7 * 7 }}", preview)
        self.assertIn("Old", builder.public())
        builder.save(node)
        self.assertEqual(builder.public(), preview)

    def test_zip_with_unexpected_path_is_rejected(self):
        builder = Builder()
        with self.assertRaisesRegex(ValueError, "Unexpected"):
            builder.install(zip_bytes({"../block.json": "{}", "block.html": ""}))
        self.assertEqual(builder.descriptors(), {})

    def test_declared_import_runs_server_logic(self):
        plugins = Plugins()
        plugins.install(plugin(READ, ["content.read"]))
        self.assertEqual(plugins.run(), 42)
        self.assertEqual(plugins.host_calls, 1)

    def test_undeclared_permission_blocks_call(self):
        plugins = Plugins()
        plugins.install(plugin(READ))
        with self.assertRaisesRegex(wasmtime.WasmtimeError, "read_content"):
            plugins.run()
        self.assertEqual(plugins.host_calls, 0)

    def test_wasi_not_linked_even_with_cms_permission(self):
        plugins = Plugins()
        plugins.install(plugin(WASI, ["content.read"]))
        with self.assertRaisesRegex(wasmtime.WasmtimeError, "wasi_snapshot_preview1"):
            plugins.run()

    def test_loop_is_interrupted_and_host_recovers(self):
        plugins = Plugins()
        plugins.install(plugin(LOOP))
        with self.assertRaises(wasmtime.Trap) as error:
            plugins.run()
        self.assertEqual(error.exception.trap_code, wasmtime.TrapCode.OUT_OF_FUEL)
        plugins.disable()
        with self.assertRaisesRegex(ValueError, "disabled"):
            plugins.run()
        plugins.install(plugin(READ, ["content.read"]))
        self.assertEqual(plugins.run(), 42)

    def test_guest_memory_is_limited(self):
        plugins = Plugins()
        plugins.install(plugin('(module (memory 2) (func (export "run")))'))
        with self.assertRaisesRegex(wasmtime.WasmtimeError, "memory"):
            plugins.run()


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--theme":
        Path(sys.argv[2]).write_bytes(THEME)
    elif len(sys.argv) == 3 and sys.argv[1] == "--guest":
        plugins = Plugins()
        plugins.install(plugin_bytes(Path(sys.argv[2]).read_bytes(), ["content.read"]))
        result = plugins.run()
        if result != 42 or plugins.host_calls != 1:
            raise RuntimeError(f"Unexpected plugin behavior: {result}, {plugins.host_calls}")
        print("AssemblyScript plugin ZIP: result=42, allowed host calls=1")
    else:
        unittest.main()
