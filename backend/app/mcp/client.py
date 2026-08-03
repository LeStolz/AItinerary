import sys
import os
import asyncio
from contextlib import AsyncExitStack
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

# Global caches for MCP processes to prevent massive startup overhead
_mcp_sessions = {}
_mcp_exit_stacks = {}
_mcp_locks = {}

class MCPWrapper:
    """Wrapper to easily connect to a local Python MCP server via a persistent connection pool."""
    def __init__(self, server_script: str):
        # Allow passing relative paths like 'maps_server.py' or absolute paths
        if not os.path.isabs(server_script):
            self.server_path = os.path.abspath(os.path.join(os.path.dirname(__file__), server_script))
        else:
            self.server_path = server_script
            
        self.python_exe = sys.executable
        self.server_name = os.path.basename(self.server_path)
        
        if self.server_name not in _mcp_locks:
            _mcp_locks[self.server_name] = asyncio.Lock()

    async def get_session(self) -> ClientSession:
        async with _mcp_locks[self.server_name]:
            if self.server_name in _mcp_sessions:
                return _mcp_sessions[self.server_name]
                
            stack = AsyncExitStack()
            _mcp_exit_stacks[self.server_name] = stack
            
            try:
                server_params = StdioServerParameters(
                    command=self.python_exe,
                    args=[self.server_path]
                )
                read, write = await stack.enter_async_context(stdio_client(server_params))
                session = await stack.enter_async_context(ClientSession(read, write))
                await session.initialize()
                
                _mcp_sessions[self.server_name] = session
                return session
            except Exception as e:
                await stack.aclose()
                raise e

# Helper to instantiate all clients
def get_all_mcp_clients():
    return {
        "maps": MCPWrapper("maps_server.py"),
        "weather": MCPWrapper("weather_server.py"),
        "booking": MCPWrapper("booking_server.py"),
        "storage": MCPWrapper("storage_server.py")
    }
