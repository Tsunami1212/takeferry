"""Optional interoperability check using an already installed official mcp client."""
import argparse
import asyncio
import os
import sys
import tempfile
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def verify(app):
    with tempfile.TemporaryDirectory() as state:
        args = [str(app.resolve()), "serve"] if app else ["-m", "takeferry", "serve"]
        params = StdioServerParameters(command=sys.executable, args=args, env=dict(os.environ, TAKEFERRY_STATE_DIR=state))
        async with stdio_client(params) as pipes, ClientSession(*pipes) as client:
            server = await client.initialize()
            listing = await client.list_tools()
            result = await client.call_tool("takeferry_compare", {"shot": "proof/01"})
            assert server.serverInfo.name == "takeferry"
            assert any(tool.name == "takeferry_pippit_bind" for tool in listing.tools)
            assert not result.isError and result.structuredContent == {"selection": None, "takes": []}
            print(server.protocolVersion, server.serverInfo.name, len(listing.tools), "tools; shot lookup passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path)
    asyncio.run(verify(parser.parse_args().app))
