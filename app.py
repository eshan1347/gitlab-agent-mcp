import os
import sys
import mcp
import pydantic
import pydantic_ai
import logfire
from server import GitlabMCP
from pydantic_ai import Agent, RunContext, agent
from pydantic import BaseModel, Field, model_validator, field_validator
from pydantic_ai.mcp import MCPServerStdio, load_mcp_servers
from dotenv import load_dotenv
import asyncio
from typing import List, Dict, Any, Optional, Annotated
from mcp.types import Tool, TextContent
import logging

load_dotenv('./.env')
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger(__name__)

# server = MCPServerStdio(
#     command='npx',
#     args=[
#         "-y",
#         "mcp-remote",
#         "https://gitlab.com/api/v4/mcp",
#         "--static-oauth-client-metadata",
#         "{\"scope\": \"mcp\"}"
#     ],
#     env={
#         'GITLAB_PERSONAL_ACCESS_TOKEN': os.environ['GITLAB_ACCESS_TOKEN'],
#         'GITLAB_ALLOWED_PROJECT_IDS': os.environ['GITLAB_PROJECT_ID'] 
#     }
# )

server = MCPServerStdio(
    command='python',
    args=[
        'server2.py'
    ],
    env={
        'GITLAB_ACCESS_TOKEN': os.environ['GITLAB_ACCESS_TOKEN'],
        'GITLAB_PROJECT_ID': os.environ['GITLAB_PROJECT_ID']         
    }
)

# servers = load_mcp_servers('mcp_config.json')

async def main():
    logfire.configure(send_to_logfire='if-token-present')
    logfire.instrument_pydantic()
    logfire.instrument_pydantic_ai()
    logfire.instrument_google_genai()
    agent = Agent('google-gla:gemini-2.5-flash', toolsets=[server])
    qs = ['list all tools', 'list all my projects', 'get README file for project 75002825']
    async with agent:
        logger.info("Starting agent")
        try:
            for q in qs:
                res = await agent.run(q)
                logger.info(f'Answer: {res.output}')
                logger.info(f'Usage: {res.usage()}')
        except Exception as e:
            if hasattr(e, 'args') and e.args:
                logger.warning(f"Gemini Error:\n{e.args[0]}")
            if hasattr(e, '__cause__') and e.__cause__:
                logger.warning(f"Underlying cause:\n{e.__cause__}")
            raise

if __name__=='__main__':
    asyncio.run(main())
