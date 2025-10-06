import os
import sys
import mcp 
import json
import asyncio
from contextlib import AsyncExitStack
from typing import List, Dict, Any, Optional, Annotated
from dotenv import load_dotenv
# from mcp.types import Tool, TextContent
import logging

load_dotenv('./.env')
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger(__name__)

class GitlabMCP:
    GITLAB_ACCESS_TOKEN: str 
    GITLAB_PROJECT_ID: str 
    tools: List[Any]
    is_conn: bool
    session: Optional[mcp.ClientSession]
    _session_ctx: Optional[Any]
    exit_stack: AsyncExitStack
    stdio: List[Any]
    _stdio_ctx: Any

    def __init__(self, GITLAB_ACCESS_TOKEN='', GITLAB_PROJECT_ID=''):
        self.GITLAB_ACCESS_TOKEN = GITLAB_ACCESS_TOKEN
        self.GITLAB_PROJECT_ID = GITLAB_PROJECT_ID
        self.tools = []
        self.is_conn = False
        self.session = None
        self._session_ctx = None
        self.exit_stack = AsyncExitStack()
        self.stdio = [None, None]
        self._stdio_ctx = None

    async def _connect(self):
        try: 
            if not self.is_conn:
                server_params = mcp.StdioServerParameters(
                    command='npx',
                    args=[
                        "-y", 
                        "@zereight/mcp-gitlab"
                    ],
                    env={
                        'GITLAB_PERSONAL_ACCESS_TOKEN': self.GITLAB_ACCESS_TOKEN,
                        'GITLAB_ALLOWED_PROJECT_IDS': self.GITLAB_PROJECT_ID 
                    }
                )
                self._stdio_ctx = mcp.client.stdio.stdio_client(server_params)
                self.stdio = await self._stdio_ctx.__aenter__()
                self._session_ctx = mcp.ClientSession(*self.stdio)
                self.session= await self._session_ctx.__aenter__()

                await self.session.initialize()
                self.is_conn = True
                logger.info(f'Connected successfully !')
            else:
                logger.info(f'Connection already exists !')

        except Exception as e:
            logger.exception(f'Error connecting to unoff gitlab server: {e}')

    async def disconnect(self):
        try:
            if self._session_ctx:
                await self._session_ctx.__aexit__(None, None, None)
                self._session_ctx = None
            if self._stdio_ctx:
                await self._stdio_ctx.__aexit__(None, None, None)
                self.is_conn = False
                logger.info(f'Connection closed !')
            self.stdio = None
            self.session = None 
        except Exception as e:
            logger.exception(f'Error disconnecting from unoff gitlab server: {e}')            

    async def get_tools(self) -> List[Any]:
        if self.is_conn:
            if self.tools:
                return self.tools
            resp = await self.session.list_tools()
            tools = resp.tools
            self.tools = tools
            return tools
        logger.info(f'Not connected to the server !')
        return []

    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        if self.is_conn:
            try:
                res = await self.session.call_tool(tool_name, arguments=args)
                return res
            except Exception as e:
                logger.exception(f'Error calling tool {tool_name}: {e}')      
                return 'Error! Try Again'       

async def main():
    gitlabMCP = GitlabMCP(os.environ['GITLAB_ACCESS_TOKEN'], os.environ['GITLAB_PROJECT_ID'])
    await gitlabMCP._connect()
    tools = await gitlabMCP.get_tools()
    logger.info(f'Tools: {len(tools)}')
    for tool in tools:
        logger.info(f'Tool: {tool}')
    await gitlabMCP.disconnect()

if __name__=='__main__':
    asyncio.run(main())