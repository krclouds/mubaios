#!/usr/bin/env python3
"""Tiny helper to talk to a QEMU guest over a TCP serial port."""
import re
import socket
import time

PORT = 4477


def connect(port=PORT, timeout=40):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            s = socket.create_connection(("127.0.0.1", port), timeout=5)
            s.settimeout(0.5)
            return s
        except OSError:
            time.sleep(0.2)
    raise RuntimeError("could not connect to the serial socket")


class Console:
    def __init__(self, sock):
        self.sock = sock
        self.buffer = ""
        self.transcript = ""

    def read_until(self, pattern, timeout=60):
        deadline = time.time() + timeout
        rx = re.compile(pattern)
        while time.time() < deadline:
            if rx.search(self.buffer):
                return True
            try:
                data = self.sock.recv(4096)
                if not data:
                    break
                chunk = data.decode("utf-8", "replace")
                self.buffer += chunk
                self.transcript += chunk
            except socket.timeout:
                continue
        return rx.search(self.buffer) is not None

    def send(self, line):
        self.sock.sendall(line.encode() + b"\r")
