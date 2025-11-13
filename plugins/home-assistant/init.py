import json
import logging
import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from default_tags import DEFAULT_TAGS

# converts mcp property object to manifest json
def format_property(name, prop):
    desc = prop.get("description", name)
    prop_type = prop.get("type", None)
    if prop.get("anyOf"):
        # goodenoughfornow
        prop_type = "|".join([sub_prop["type"] for sub_prop in prop["anyOf"]])
    if prop_type == "array":
        desc += f" (must be a JSON array)"
        if prop["items"].get("enum"):
            desc += f" (each item must be in enum: {prop['items']['enum']})"
    if prop.get("enum"):
        desc += f" (must be in enum: {prop['enum']})"
    if "minimum" in prop:
        desc += f" (minimum: {prop['minimum']})"
    if "maximum" in prop:
        desc += f" (maximum: {prop['maximum']})"
    return {
        "type": prop_type,
        "description": desc
    }

# converts mcp tool object to manifest json
def format_tool(tool):
    ret = {
        "name": tool.name,
        "description": tool.description,
        "tags": DEFAULT_TAGS.get(tool.name, []),
        "properties": {name: format_property(name, prop) for name, prop in tool.inputSchema["properties"].items()}
    }
    return ret

async def populate_manifest(url: str, bearer_token: str):
    # Connect to a streamable HTTP server
    async with streamablehttp_client(
        url,
        headers={"Authorization": f"Bearer {bearer_token}"}
    ) as (
        read_stream,
        write_stream,
        _,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            formatted_tools = []
            for tool in tools.tools:
                try:
                    formatted_tool = format_tool(tool)
                    if formatted_tool["name"] == "GetLiveContext":
                        live_context = await session.call_tool("GetLiveContext")
                        result = json.loads(live_context.content[0].text)["result"]
                        formatted_tool["description"] += f"\nLast {result}"
                    formatted_tools.append(formatted_tool)
                except:
                    pass
            try:
                with open("manifest_template.json") as f:
                    manifest = json.load(f)
            except:
                manifest = json.loads("{'manifestVersion': 1, 'executable': './home-assistant-plugin.exe', 'persistent': True, 'passthrough': False, 'functions': []}")
            manifest["functions"] = formatted_tools
            # write to manifest.json
            with open("manifest.json", "w") as f:
                json.dump(manifest, f, indent=4)

if __name__ == "__main__":
    print("running manifest initialization...")
    with open("config.json") as f:
        config = json.load(f)
    if not config.get("homeassistant_access_token", None):
        print("homeassistant_access_token is missing from config.")
    if not config.get("homeassistant_mcp_url", None):
        print("homeassistant_mcp_url is missing from config.")
    try:
        asyncio.run(populate_manifest(config["homeassistant_mcp_url"], config["homeassistant_access_token"]))
    except Exception as e:
        print(f"Error initializing plugin: {e}")
        raise
    print("initialized.")