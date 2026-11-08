#!/usr/bin/env python3
"""Minimal QMP client for driving a QEMU guest: input injection and screenshots."""
import json
import os
import socket
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
QEMU = os.path.join(os.path.dirname(ROOT), "tinylinux", "out", "toolchain", "msys64",
                    "ucrt64", "bin", "qemu-system-x86_64.exe")

QMP_PORT = 4451
SERIAL_PORT = 4452

CHARS = {
    " ": "spc", "-": "minus", "=": "equal", ".": "dot", ",": "comma",
    "/": "slash", "_": "shift-minus", ":": "shift-semicolon",
}


class QMP:
    def __init__(self, port=QMP_PORT, timeout=40, device="/machine/peripheral/nova-tablet"):
        self.device = device
        deadline = time.time() + timeout
        self.sock = None
        while time.time() < deadline:
            try:
                self.sock = socket.create_connection(("127.0.0.1", port), timeout=5)
                break
            except OSError:
                time.sleep(0.2)
        if not self.sock:
            raise RuntimeError("QMP connect failed")
        self.f = self.sock.makefile("rwb")
        self._read()  # greeting
        self.cmd("qmp_capabilities")

    def _read(self):
        while True:
            line = self.f.readline()
            if not line:
                raise RuntimeError("QMP closed")
            msg = json.loads(line)
            if "event" in msg:
                continue
            return msg

    def cmd(self, name, **args):
        payload = {"execute": name}
        if args:
            payload["arguments"] = args
        self.f.write((json.dumps(payload) + "\r\n").encode())
        self.f.flush()
        resp = self._read()
        if "error" in resp:
            raise RuntimeError("%s: %s" % (name, resp["error"]))
        return resp.get("return")

    def _args(self, events):
        args = {"events": events}
        if self.device:
            args["device"] = self.device
        return args

    def abs_pos(self, x, y):
        self.cmd("input-send-event", **self._args([
            {"type": "abs", "data": {"axis": "x", "value": x}},
            {"type": "abs", "data": {"axis": "y", "value": y}},
        ]))

    def click(self, x, y, hold=0.06):
        self.abs_pos(x, y)
        time.sleep(0.02)
        self.cmd("input-send-event", **self._args([
            {"type": "btn", "data": {"down": True, "button": "left"}},
        ]))
        time.sleep(hold)
        self.cmd("input-send-event", **self._args([
            {"type": "btn", "data": {"down": False, "button": "left"}},
        ]))

    def drag(self, x0, y0, x1, y1, steps=12):
        self.abs_pos(x0, y0)
        self.cmd("input-send-event", **self._args([
            {"type": "btn", "data": {"down": True, "button": "left"}},
        ]))
        for i in range(1, steps + 1):
            self.abs_pos(x0 + (x1 - x0) * i // steps, y0 + (y1 - y0) * i // steps)
            time.sleep(0.02)
        self.cmd("input-send-event", **self._args([
            {"type": "btn", "data": {"down": False, "button": "left"}},
        ]))

    @staticmethod
    def _k(code, down):
        return {"type": "key", "data": {"down": down, "key": {"type": "qcode", "data": code}}}

    def key(self, qcode, shift=False):
        if shift:
            self.cmd("input-send-event", events=[self._k("shift", True)])
        self.cmd("input-send-event", events=[self._k(qcode, True)])
        self.cmd("input-send-event", events=[self._k(qcode, False)])
        if shift:
            self.cmd("input-send-event", events=[self._k("shift", False)])
        time.sleep(0.03)

    def type_text(self, text):
        for ch in text:
            if ch in CHARS:
                code = CHARS[ch]
                if code.startswith("shift-"):
                    self.key(code.split("-", 1)[1], shift=True)
                else:
                    self.key(code)
            elif ch.isupper():
                self.key(ch.lower(), shift=True)
            else:
                self.key(ch)

    def screendump(self, path):
        self.cmd("screendump", filename=path)


def start_vm(extra_args=(), serial="file", accel="whpx"):
    log = os.path.join(ROOT, "out", "nova-serial.log")
    if os.path.exists(log):
        os.remove(log)
    args = [
        QEMU, "-m", "512", "-smp", "2",
        "-kernel", os.path.join(ROOT, "out", "nova.bzImage"),
        "-initrd", os.path.join(ROOT, "out", "nova-initramfs.cpio.gz"),
        "-append", "console=ttyS0 rdinit=/init loglevel=4 vt.global_cursor_default=0",
        "-vga", "std",
        "-display", "none", "-monitor", "none",
        "-qmp", "tcp:127.0.0.1:%d,server=on,wait=off" % QMP_PORT,
        "-serial", ("tcp:127.0.0.1:4477,server=on,wait=off" if serial == "tcp" else "file:" + log),
        "-net", "none", "-no-reboot",
    ] + list(extra_args)
    if accel:
        args += ["-accel", accel]
    proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    if accel:
        time.sleep(1.0)
        if proc.poll() is not None:
            args = [a for a in args if a not in ("-accel", accel)]
            proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    return proc


def wait_serial(marker, timeout=60):
    path = os.path.join(ROOT, "out", "nova-serial.log")
    deadline = time.time() + timeout
    while time.time() < deadline:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    if marker in f.read():
                        return True
            except OSError:
                pass
        time.sleep(0.3)
    return False
