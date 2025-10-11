from pydantic_ai.mcp import MCPServerStdio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import asyncio
from typing import List, Dict, Any, Optional, Annotated
from mcp.types import Tool, TextContent, CallToolResult
from server import GitlabMCP
import os 
import sys
import mcp
import logging
from utils2 import jsonConv
# from google import genai

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger(__name__)
# mcp_server = mcp.server.FastMCP('gitlab-agent-server')
gitlabMCP = GitlabMCP(os.environ['GITLAB_ACCESS_TOKEN'], os.environ['GITLAB_PROJECT_ID'])

# @asynccontextmanager
# async def server_lifespan(_server: mcp.server.Server) -> AsyncIterator[Dict[str, GitlabMCP]]:
#     gitlabMCP = GitlabMCP(os.environ['GITLAB_ACCESS_TOKEN'], os.environ['GITLAB_PROJECT_ID'])
#     await gitlabMCP._connect()
#     try: 
#         yield {'server': gitlabMCP}
#     finally: 
#         await gitlabMCP.disconnect()

mcp_server = mcp.server.Server('gitlab-agent-server') #lifespan=server_lifespan)

@mcp_server.list_tools()
async def list_tools() -> List[Optional[Tool]]:
    """List all available Gitlab tools"""

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
    logger.info(f'call_tool (name: {name}, arguments: \n {arguments})')    
    res = await gitlabMCP.call_tool(name, arguments)
    logger.info(f'call_tool res: \n{res}')
    return [TextContent(type='text', text=res)] if isinstance(res, str) else [TextContent(type='text', text=str(res.content))]

# @mcp_server.tool()
# async def search_repositories(project_name: str) -> List[TextContent]:
#     res = await gitlabMCP.call_tool('search_repositories', args={'search': project_name})
#     # print(f'{type(res)} | Projects: \n{res}')
#     return res.content

# @mcp_server.tool()
# async def get_project_details(project_id: int) -> List[TextContent]:
#     res = await gitlabMCP.call_tool('get_project', args={'project_id': str(project_id)})
#     return res.content

async def main():
    try:
        await gitlabMCP._connect()
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options()
            )
    finally: 
        await gitlabMCP.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
