"""
MCP Client - Connects to MCP servers and uses their tools
"""
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack
import asyncio
from typing import Optional, List, Dict, Any
import json

class MCPClient:
    """Client for connecting to MCP servers"""

    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.available_tools = []
        self.available_resources = []
        self.server_info = {}
        self.connected = False

    async def connect_to_server(self, server_script_path: str, args: List[str] = None):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the MCP server script
            args: Additional arguments for the server
        """
        try:
            # Determine if server is Python or Node
            is_python = server_script_path.endswith('.py')

            command = "python" if is_python else "node"
            server_args = [server_script_path]
            if args:
                server_args.extend(args)

            server_params = StdioServerParameters(
                command=command,
                args=server_args,
                env=None
            )

            # Create stdio transport
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )

            # Initialize session
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(stdio_transport[0], stdio_transport[1])
            )

            # Initialize the connection
            result = await self.session.initialize()
            self.server_info = {
                'name': result.serverInfo.name if hasattr(result, 'serverInfo') else 'Unknown',
                'version': result.serverInfo.version if hasattr(result, 'serverInfo') else 'Unknown'
            }

            # List available tools
            tools_response = await self.session.list_tools()
            self.available_tools = [
                {
                    'name': tool.name,
                    'description': tool.description if hasattr(tool, 'description') else '',
                    'parameters': tool.inputSchema if hasattr(tool, 'inputSchema') else {}
                }
                for tool in tools_response.tools
            ]

            # List available resources
            try:
                resources_response = await self.session.list_resources()
                self.available_resources = [
                    {
                        'uri': res.uri,
                        'name': res.name if hasattr(res, 'name') else '',
                        'description': res.description if hasattr(res, 'description') else ''
                    }
                    for res in resources_response.resources
                ]
            except:
                self.available_resources = []

            self.connected = True

            print(f"✓ Connected to MCP server: {self.server_info.get('name')}")
            print(f"  Available tools: {len(self.available_tools)}")
            print(f"  Available resources: {len(self.available_resources)}")

            return True

        except Exception as e:
            print(f"✗ Failed to connect to MCP server: {e}")
            self.connected = False
            return False

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server

        Args:
            tool_name: Name of the tool to call
            arguments: Dictionary of arguments for the tool

        Returns:
            Tool execution result
        """
        if not self.session or not self.connected:
            raise RuntimeError("Not connected to MCP server")

        try:
            result = await self.session.call_tool(tool_name, arguments)

            # Extract content from result
            if hasattr(result, 'content') and result.content:
                content = result.content[0]
                if hasattr(content, 'text'):
                    return {'success': True, 'result': content.text}
                else:
                    return {'success': True, 'result': str(content)}

            return {'success': True, 'result': str(result)}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def get_available_tools(self) -> List[Dict]:
        """Get list of available tools

        Returns:
            List of tool information dictionaries
        """
        if not self.connected:
            return []

        return self.available_tools

    async def get_tool_info(self, tool_name: str) -> Optional[Dict]:
        """Get information about a specific tool

        Args:
            tool_name: Name of the tool

        Returns:
            Tool information or None
        """
        for tool in self.available_tools:
            if tool['name'] == tool_name:
                return tool
        return None

    async def get_resource(self, uri: str) -> Optional[str]:
        """Get a resource from the MCP server

        Args:
            uri: Resource URI (e.g., 'config://settings')

        Returns:
            Resource content
        """
        if not self.session or not self.connected:
            raise RuntimeError("Not connected to MCP server")

        try:
            result = await self.session.read_resource(uri)
            if hasattr(result, 'contents') and result.contents:
                content = result.contents[0]
                if hasattr(content, 'text'):
                    return content.text
                else:
                    return str(content)
            return None
        except Exception as e:
            print(f"Error reading resource {uri}: {e}")
            return None

    async def get_available_resources(self) -> List[Dict]:
        """Get list of available resources

        Returns:
            List of resource information dictionaries
        """
        return self.available_resources

    async def disconnect(self):
        """Disconnect from the MCP server"""
        try:
            await self.exit_stack.aclose()
            self.connected = False
            print("✓ Disconnected from MCP server")
        except Exception as e:
            print(f"Error during disconnect: {e}")

    def is_connected(self) -> bool:
        """Check if connected to a server

        Returns:
            True if connected
        """
        return self.connected

# Singleton instance
_mcp_client_instance = None

def get_mcp_client() -> MCPClient:
    """Get the global MCP client instance

    Returns:
        MCPClient instance
    """
    global _mcp_client_instance
    if _mcp_client_instance is None:
        _mcp_client_instance = MCPClient()
    return _mcp_client_instance

# Usage example
async def main():
    """Example usage of MCP client"""
    client = get_mcp_client()

    try:
        # Connect to server
        success = await client.connect_to_server("services/mcp_server.py")

        if not success:
            print("Failed to connect to server")
            return

        # List tools
        tools = await client.get_available_tools()
        print(f"\nAvailable tools ({len(tools)}):")
        for tool in tools:
            print(f"  - {tool['name']}: {tool.get('description', 'No description')}")

        # Call a tool
        print("\nTesting add_numbers tool:")
        result = await client.call_tool("add_numbers", {"a": 5, "b": 3})
        print(f"  Result: {result}")

        # Call another tool
        print("\nTesting get_current_time tool:")
        result = await client.call_tool("get_current_time", {})
        print(f"  Result: {result}")

        # Get a resource
        print("\nGetting config resource:")
        config = await client.get_resource("config://settings")
        print(f"  Config: {config}")

    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
