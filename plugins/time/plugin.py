import json
import sys
import requests
import logging
import os
from ctypes import byref, windll, wintypes
from typing import Optional, Dict, Any
from datetime import datetime

# Type definitions
Response = Dict[bool, Optional[str]]


# Configure logging with a more detailed format
LOG_FILE = os.path.join(os.environ.get('USERPROFILE', '.'), 'time-plugin.log')
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
)

def get_time() -> dict:
    """
    Retrieves the current local time.
        
    Returns:
        dict: A dictionary containing:
            - success (bool): Whether the operation was successful
            - message (str): Current local time or error message
            
    Example:
        >>> get_time()
        {
            "success": True,
            "message": "2025-11-11 21:08:27.569055"
        }
        
    Raises:
        No exceptions are raised. All errors are caught and returned in the response dict.
    """
    return {"success": True, "message": str(datetime.now())}

def main():
    """
    Main entry point for the time plugin.
    
    Sets up command handling and maintains the main event loop for processing commands.
    The plugin supports the following commands:
        - initialize: Initializes the plugin
        - shutdown: Terminates the plugin
        - get_time: Retrieves the current local time
        
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
        'initialize': lambda _: {"success": True, "message": "Plugin initialized"},
        'shutdown': lambda _: {"success": True, "message": "Plugin shutdown"},
        'get_time': get_time,
    }
    
    while True:
        command = read_command()
        if command is None:
            logging.error('Error reading command')
            continue
        
        tool_calls = command.get("tool_calls", [])
        for tool_call in tool_calls:
            logging.info(f"Tool call: {tool_call}")
            func = tool_call.get("func")
            logging.info(f"Function: {func}")
            params = tool_call.get("params", {})
            logging.info(f"Params: {params}")
            
            if func in commands:
                response = commands[func](params)
            else:
                response = {'success': False, 'message': "Unknown function call"}
            
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


if __name__ == '__main__':
    main()
