from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from contextlib import AsyncExitStack
from contextlib import AsyncExitStack
import os
import json
import sys

mcp_clients = None

class MCPClient:
    def __init__(self):
        self.session = None
        self.exit_stack = AsyncExitStack()
        self.tools = []
        self.tool_names = []

    async def connect_to_server(self, server_info):
        """連接 MCP 伺服器

        Args:
            server_info: MCP 伺服器的連接資訊
        """
        if "url" in server_info[1]:
            streams = await (
                self.exit_stack.enter_async_context(
                    sse_client(**server_info[1])
                )
            )
        else:
            server_params = StdioServerParameters(**server_info[1])

            streams = await (
                self.exit_stack.enter_async_context(
                    stdio_client(server_params)
                )
            )
        self.session = await (
            self.exit_stack.enter_async_context(
                ClientSession(*streams)
            )
        )

        await self.session.initialize()

        # 取得 MCP 伺服器提供的工具資訊
        response = await self.session.list_tools()
        tools = response.tools
        self.tools = [{
            "type": "function",
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.inputSchema
        } for tool in tools]
        self.tool_names = [tool.name for tool in tools]

        print('-' * 20)
        print(f"已連接 {server_info[0]} 伺服器")
        print('\n'.join(
            [f'    - {name}' for name in self.tool_names]
        ))
        print('-' * 20)

    async def cleanup(self):
        """釋放資源"""
        await self.exit_stack.aclose()

async def load_mcp_servers():
    global mcp_clients
    
    if (not os.path.exists("mcp_servers.json") or
        not os.path.isfile("mcp_servers.json")):
        print("Error:找不到 mcp_servers.json 檔", file=sys.stderr)
        return []
    
    with open("mcp_servers.json", "r", encoding="utf-8") as f:
        try:
            server_infos = tuple(
                json.load(f)['mcpServers'].items()
            )
        except:
            print(
                "Error: mcp_servers.json 檔案格式錯誤", 
                file=sys.stderr
            )
            return []
    
    if len(server_infos) == 0:
        print(
            "Error: mcp_servers.json 檔案內沒有任何伺服器", 
            file=sys.stderr
        )
        return []
    
    mcp_clients = []
    for server_info in server_infos:
        try:
            client = MCPClient()
            await client.connect_to_server(server_info)
            mcp_clients.append(client)
        except Exception as e:
            print(
                f"連不上 {server_info[0]}: {e}", 
                file=sys.stderr
            )
            
    tools = []
    for client in mcp_clients:
        tools += client.tools
    return tools

async def unload_mcp_servers():
    global mcp_clients
    if mcp_clients is None:
        return
    for client in mcp_clients[::-1]:
        await client.cleanup()
        
async def call_tools(tool_calls):
    global mcp_clients
    
    # 處理回應並執行工具
    messages = []

    for output in tool_calls:
        if output.type != 'function_call':
            continue
        tool_name = output.name
        tool_args = eval(output.arguments)
        for client in mcp_clients:
            if tool_name in client.tool_names:
                break
        else:
            # 如果沒有找到對應的工具，則跳過這個迴圈
            continue
        result = await client.session.call_tool(
            tool_name, tool_args
        )

        messages.append({
            # 建立可傳回函式執行結果的字典
            "type": "function_call_output", # 設為工具輸出類型的訊息
            "call_id": output.call_id, # 叫用函式的識別碼
            "output": result.content[0].text # 函式傳回值
        })
    
    return messages
