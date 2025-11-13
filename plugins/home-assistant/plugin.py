"""
Example Command Format:
    {
        "tool_calls": [
            {
                "func": "a",
                "params": {"b": "c"}
            }
        ]
    }

Example Response Format:
    {
        "success": true,
        "message": ""
    }
"""

import json
import requests
import logging
import os
from ctypes import byref, windll, wintypes
from typing import Optional, Dict, Any
import asyncio
import ast

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from init import populate_manifest


config = {}
manifest = {}

Response = Dict[bool, Optional[str]]


# Configure logging with a more detailed format
LOG_FILE = os.path.join(os.environ.get('USERPROFILE', '.'), 'home-assistant-plugin.log')
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
)

def eval_param(func, property, param):
    global manifest
    for function in manifest.get("functions", []):
        if function.get("name") == func:
            if property in function.get("properties", {}):
                desired_type = function["properties"][property]["type"]
                if desired_type == "array":
                    try:
                        evaled = ast.literal_eval(param)
                        if isinstance(evaled, (list, tuple)):
                            return list(evaled)
                    except (ValueError, SyntaxError):
                        return param
                elif desired_type == "integer":
                    try:
                        return int(param)
                    except (ValueError, TypeError):
                        return param
                elif desired_type == "number":
                    try:
                        return float(param)
                    except (ValueError, TypeError):
                        return param
                else:
                    return param
    return param

def initialize():
    logging.info("initializing...")
    global config
    global manifest
    with open("config.json") as f:
        config = json.load(f)
    # try:
    #     asyncio.run(populate_manifest(config["homeassistant_mcp_url"], config["homeassistant_access_token"]))
    # except Exception as e:
    #     logging.error(f"Error initializing plugin: {e}")
    #     return {"success": False, "message": str(e)}
    with open("manifest.json") as f:
        manifest = json.load(f)
    logging.info("initialized.")

async def call_tool_async(func: str, params: dict) -> dict:
    async with streamablehttp_client(
        config["homeassistant_mcp_url"],
        headers={"Authorization": f"Bearer {config["homeassistant_access_token"]}"}
    ) as (
        read_stream,
        write_stream,
        _,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            response = await session.call_tool(func, {key: eval_param(func, key, value) for key, value in params.items()})
            logging.info(f"Tool call response for {func}: {response}")
            return response.content[0].text

def call_tool(func: str, params: dict) -> dict:
    logging.info(f"Calling tool: {func} with params: {params}")
    try:
        result = asyncio.run(call_tool_async(func, params))
        return {"success": True, "message": str(result)}
    except Exception as e:
        logging.error(f"Error calling tool: {e}")
        return {"success": False, "message": str(e)}

def main():
    """
    Main entry point for the plugin.
    
    Sets up command handling and maintains the main event loop for processing commands.
    The plugin supports the following commands:
        - initialize: Initializes the plugin
        - shutdown: Terminates the plugin
        
    The function continues running until a shutdown command is received.
    
    Command Processing:
        1. Reads input from standard input
        2. Parses the JSON command
        3. Executes the appropriate function
        4. Writes the response to standard output
        
    Error Handling:
        - Invalid commands are logged and ignored
        - Communication errors are logged
        - All errors are caught and handled gracefully
    """

    commands = {
        'initialize': lambda _: logging.info("hello"),
        'shutdown': lambda _: logging.info("goodbye")
    }
    
    while True:
        command = read_command()
        logging.info(f"Received command: {command}")
        tool_calls = command.get("tool_calls", [])
        for tool_call in tool_calls:
            func = tool_call.get("func")
            params = tool_call.get("params", {})
            if func in commands:
                response = commands[func](params)
            else:
                response = call_tool(func, params)
            write_response(response)
    
def read_command() -> dict | None:
    ''' Reads a command from the communication pipe.

    Returns:
        Command details if the input was proper JSON; `None` otherwise
    '''
    try:
        STD_INPUT_HANDLE = -10
        pipe = windll.kernel32.GetStdHandle(STD_INPUT_HANDLE)

        # Read in chunks until we get the full message
        chunks = []
        while True:
            BUFFER_SIZE = 4096
            message_bytes = wintypes.DWORD()
            buffer = bytes(BUFFER_SIZE)
            success = windll.kernel32.ReadFile(
                pipe,
                buffer,
                BUFFER_SIZE,
                byref(message_bytes),
                None
            )

            if not success:
                logging.error('Error reading from command pipe')
                return None
            
            # Add the chunk we read
            chunk = buffer.decode('utf-8')[:message_bytes.value]
            chunks.append(chunk)

             # If we read less than the buffer size, we're done
            if message_bytes.value < BUFFER_SIZE:
                break

        # Combine all chunks and parse JSON
        retval = ''.join(chunks)
        return json.loads(retval)

    except json.JSONDecodeError:
        logging.error(f'Received invalid JSON: {retval}')
        return None
    except Exception as e:
        logging.error(f'Exception in read_command(): {str(e)}')
        return None


def write_response(response:Response) -> None:
    ''' Writes a response to the communication pipe.

    Parameters:
        response: Response
    '''
    try:
        STD_OUTPUT_HANDLE = -11
        pipe = windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

        json_message = json.dumps(response) + '<<END>>'
        message_bytes = json_message.encode('utf-8')
        message_len = len(message_bytes)

        bytes_written = wintypes.DWORD()
        success = windll.kernel32.WriteFile(
            pipe,
            message_bytes,
            message_len,
            bytes_written,
            None
        )

        if not success:
            logging.error('Error writing to response pipe')

    except Exception as e:
        logging.error(f'Exception in write_response(): {str(e)}')

initialize()

if __name__ == '__main__':
    main()
