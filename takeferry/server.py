"""A newline-delimited JSON-RPC MCP server on stdin/stdout."""
from __future__ import annotations

import json
import sqlite3
import sys

from . import __version__
from .brief import TakeError
from .tools import TOOLS, dispatch

VERSIONS = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")


class Session:
    def __init__(self, studio):
        self.studio = studio
        self.version = None

    def process(self, message):
        req_id = message.get("id") if isinstance(message, dict) else None
        def error(code, description):
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": description}}
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str):
            return error(-32600, "Invalid JSON-RPC request.")
        if "id" not in message:
            return None
        if type(req_id) not in (int, str):
            return error(-32600, "Expected a string or integer request ID.")
        method, params = message["method"], message.get("params", {})
        if not isinstance(params, dict):
            return error(-32602, "Expected named parameters.")
        if method == "initialize":
            version = params.get("protocolVersion")
            self.version = version if version in VERSIONS else VERSIONS[0]
            result = {"protocolVersion": self.version, "serverInfo": {"name": "takeferry", "version": __version__},
                      "capabilities": {"tools": {"listChanged": False}}}
        elif method == "ping":
            result = {}
        elif not self.version:
            return error(-32002, "Initialize the MCP session first.")
        elif method == "tools/list":
            result = {"tools": [spec for _, spec in TOOLS.values()]}
        elif method == "tools/call":
            name = params.get("name")
            if not isinstance(name, str) or name not in TOOLS:
                return error(-32602, "Unknown tool name.")
            try:
                data = dispatch(self.studio, name, params.get("arguments", {}))
                result = {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False, allow_nan=False)}], "isError": False}
                if self.version in VERSIONS[:2]:
                    result["structuredContent"] = data
            except (TakeError, OSError, sqlite3.Error, ValueError) as exc:
                result = {"content": [{"type": "text", "text": str(exc)}], "isError": True}
        else:
            return error(-32601, "Method not found.")
        return {"jsonrpc": "2.0", "id": req_id, "result": result}


def serve(studio):
    session = Session(studio)
    for line in sys.stdin.buffer:
        try:
            message = json.loads(line)
        except (ValueError, UnicodeError):
            answer = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error."}}
        else:
            answer = session.process(message)
        if answer is not None:
            print(json.dumps(answer, ensure_ascii=True, allow_nan=False), flush=True)
