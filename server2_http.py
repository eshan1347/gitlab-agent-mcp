from pydantic_ai.mcp import MCPServerStdio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import asyncio
import uvicorn
import contextlib
from typing import List, Dict, Any, Optional, Annotated
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import StreamingResponse
from mcp.types import Tool, TextContent, CallToolResult
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.middleware.cors import CORSMidlleware
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send
from server import GitlabMCP
import os 
import sys
import mcp
import logging
from utils2 import jsonConv
from google import genai

def main():
  port=3000
  json_response=True

  logging.basicConfig(stream=sys.stderr, level=logging.INFO)
  logger = logging.getLogger(__name__)
  state: Dict[str, Any] = {}
  
  mcp_server = mcp.server.Server('gitlab-agent-server')
  
  @mcp_server.list_tools()
  async def list_tools() -> List[Optional[Tool]]:
      """List all available Gitlab tools"""
      gitlabMCP = state.get('gitlabMCP')
      tools = await gitlabMCP.get_tools()
      res = []
      for i, tool in enumerate(tools[:]):
          # if i not in [47, 48, 49, 50]: #not 16, 22, 23, 29, 47, 48
              try:
                  name = tool.name
                  if not name:
                      continue
                  description = tool.description
                  ipS = jsonConv(tool.inputSchema) if tool.inputSchema else {'type': 'object', 'properties': {}, 'required': []}
                  # logger.info(f'Tool {i}: \nOg:{tool.inputSchema} \nfixed:{ipS}')
                  temp = Tool(name=name, description=description, inputSchema=ipS)
              except Exception as e:
                  async def dummy_callable(**kwargs): 
                      return None
                  temp = Tool(name=name, description=description, inputSchema=ipS, callable=dummy_callable)
                  logger.warning(f'Oops {i} \n{tool}\n{"_"*40}: {e}')
              res.append(temp)
      logger.info(f'list_tools: {len(res)}')
      return res
  
  @mcp_server.call_tool()
  async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
      """Execute a tool and return results"""
      gitlabMCP = state.get('gitlabMCP')
      logger.info(f'call_tool (name: {name}, arguments: \n {arguments})')    
      res = await gitlabMCP.call_tool(name, arguments)
      logger.info(f'call_tool res: \n{res}')
      return [TextContent(type='text', text=res)] if isinstance(res, str) else [TextContent(type='text', text=str(res.content))]

  @asynccontextmanager
  async def server_lifespan(_server: mcp.server.Server) -> AsyncIterator[Dict[str, GitlabMCP]]:
      async with session_manager.run():
        logger.info('Streamable HTTP server started !')
        gitlabMCP = GitlabMCP(os.environ['GITLAB_ACCESS_TOKEN'], os.environ['GITLAB_PROJECT_ID'])
        await gitlabMCP._connect()
        logger.info('Original Gitlab MCP connected !')
        state['gitlabMCP'] = gitlabMCP
        try: 
            yield state
        finally: 
            await gitlabMCP.disconnect()
            logger.info('Server shutting down ...')

  session_manager = StreamableHTTPSessionManager(
    app=mcp_server,
    event_store=None,
    json_response=json_response,
    stateless=True
  )

  async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
      await session_manager.handle_request(scope, receive, send)

  starlette_app = Starlette(
    debug=True,
    routes=[
      Mount("/mcp", app=handle_streamable_http),
    ],
    lifespan=server_lifespan
  )

  uvicorn.run(starlette_app, host="127.0.0.1", port=port)
  
if __name__ == '__main__':
  main()
