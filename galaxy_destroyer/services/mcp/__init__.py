"""MCP Client support for Galaxy Destroyer"""

import json
import subprocess
import asyncio
import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class MCPTool:
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str


@dataclass
class MCPResource:
    uri: str
    name: str
    mime_type: Optional[str] = None
    description: Optional[str] = None


class MCPClient:
    def __init__(self):
        self._servers: Dict[str, Any] = {}
        self._tools: Dict[str, MCPTool] = {}
        self._resources: Dict[str, MCPResource] = {}

    def add_server(self, name: str, config: Dict):
        self._servers[name] = config
        self._discover_tools(name)

    def _discover_tools(self, server_name: str):
        config = self._servers.get(server_name)
        if not config:
            return

        command = config.get("command", "")
        args = config.get("args", [])
        env = config.get("env", {})

        try:
            result = subprocess.run(
                [command] + args + ["--info"],
                env={**os.environ, **env},
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                info = json.loads(result.stdout)
                for tool in info.get("tools", []):
                    self._tools[tool["name"]] = MCPTool(
                        name=tool["name"],
                        description=tool.get("description", ""),
                        input_schema=tool.get("inputSchema", {}),
                        server_name=server_name,
                    )
        except Exception:
            pass

    async def call_tool(self, name: str, arguments: Dict) -> Dict:
        tool = self._tools.get(name)
        if not tool:
            return {"error": f"Tool not found: {name}"}

        server_config = self._servers.get(tool.server_name)
        if not server_config:
            return {"error": f"Server not configured: {tool.server_name}"}

        try:
            proc = await asyncio.create_subprocess_exec(
                server_config["command"],
                *server_config.get("args", []),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, **server_config.get("env", {})},
            )

            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": name,
                    "arguments": arguments,
                },
            }

            stdout, stderr = await proc.communicate(input=json.dumps(request).encode())

            if stderr:
                return {"error": stderr.decode()}

            response = json.loads(stdout.decode())
            return response.get("result", response)

        except Exception as e:
            return {"error": str(e)}

    def list_tools(self) -> List[MCPTool]:
        return list(self._tools.values())

    def list_resources(self) -> List[MCPResource]:
        return list(self._resources.values())

    async def read_resource(self, uri: str) -> Optional[str]:
        resource = self._resources.get(uri)
        if not resource:
            return None

        return f"Resource: {resource.name}\nURI: {resource.uri}"


_mcp_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
        _load_config()
    return _mcp_client


def _load_config():
    config_path = os.path.join(
        os.path.expanduser("~"), ".galaxy_destroyer", "mcp_config.json"
    )

    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)

            for server_name, server_config in config.get("mcpServers", {}).items():
                _mcp_client.add_server(server_name, server_config)
        except Exception:
            pass


def list_mcp_tools() -> List[Dict]:
    client = get_mcp_client()
    return [
        {
            "name": t.name,
            "description": t.description,
            "input_schema": t.input_schema,
            "server": t.server_name,
        }
        for t in client.list_tools()
    ]


def list_mcp_resources() -> List[Dict]:
    client = get_mcp_client()
    return [
        {
            "uri": r.uri,
            "name": r.name,
            "mime_type": r.mime_type,
            "description": r.description,
        }
        for r in client.list_resources()
    ]


async def call_mcp_tool(name: str, arguments: Dict) -> Dict:
    client = get_mcp_client()
    return await client.call_tool(name, arguments)
