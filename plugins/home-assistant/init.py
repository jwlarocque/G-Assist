import json
import logging
import asyncio
from collections import defaultdict

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from default_tags import DEFAULT_TAGS, ALLOWED_TOOLS

# converts mcp property object to manifest json, applying overrides
def format_property(name, prop, overrides=None):
    if overrides is None:
        overrides = {}
    if "type" in overrides:
        prop_type = overrides["type"]
    else:
        prop_type = prop.get("type", None)
        if prop.get("anyOf"):
            # goodenoughfornow
            prop_type = "|".join([sub_prop["type"] for sub_prop in prop["anyOf"]])
    if "description" in overrides:
        desc = overrides["description"]
    else:
        desc = prop.get("description", name)
        if "type" not in overrides and prop_type == "array":
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


def transform_device_list_string(device_list_string: str) -> str:
    if 'Live Context:' in device_list_string:
        device_list_string = device_list_string.split(':\n', 1)[-1].strip()
    
    domain_map = defaultdict(list)
    current_name = None
    
    lines = device_list_string.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('- names:'):
            current_name = line.split(':', 1)[1].strip()
        elif line.startswith('domain:'):
            if current_name:
                domain = line.split(':', 1)[1].strip()
                domain_map[domain].append(current_name)
                current_name = None

    output_parts = []
    for domain, names in sorted(domain_map.items()):
        names_str = ', '.join(names)
        output_parts.append(f"{domain}: {names_str}")
    return "\n\nThis is a list of available devices, with a domain on each line followed by the names of all devices in that domain. You MUST use only the names of devices found in this list for Hass tool calls. You MAY infer which name the user is referring to from context, if appropriate.\n" + '\n'.join(output_parts)


# converts mcp tool object to manifest json, using only allowed_properties
def format_tool(tool, allowed_properties):
    formatted_properties = {}
    for name, overrides in allowed_properties.items():
        # Find the original 'prop' schema from the tool object
        if name in tool.inputSchema["properties"]:
            prop = tool.inputSchema["properties"][name]
            # Format it, passing the overrides
            formatted_properties[name] = format_property(name, prop, overrides)
        else:
            pass
    ret = {
        "name": tool.name,
        "description": tool.description,
        # "tags": DEFAULT_TAGS.get(tool.name, []),
        "properties": formatted_properties
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
                if tool.name not in ALLOWED_TOOLS:
                    continue
                allowed_properties = ALLOWED_TOOLS[tool.name]

                try:
                    formatted_tool = format_tool(tool, allowed_properties)
                    # if formatted_tool["name"] == "GetLiveContext":
                    #     live_context = await session.call_tool("GetLiveContext")
                    #     result = json.loads(live_context.content[0].text)["result"]
                    #     formatted_tool["description"] += f"\nLast {result}"
                    formatted_tools.append(formatted_tool)
                except Exception as e:
                    print(f"Warning: Failed to format tool {tool.name}: {e}")

            try:
                with open("manifest_template.json") as f:
                    manifest = json.load(f)
            except:
                manifest = json.loads("{'manifestVersion': 1, 'executable': './home-assistant-plugin.exe', 'persistent': True, 'passthrough': False, 'description': 'Home Assistant plugin for controlling and monitoring smart home devices.', 'functions': []}")
            manifest["functions"] = formatted_tools

            manifest["description"] = "Control and monitor smart home devices."
            live_context = await session.call_tool("GetLiveContext")
            result = json.loads(live_context.content[0].text)["result"]
            manifest["description"] += transform_device_list_string(result)
            print(manifest["description"])

            # write to manifest.json
            with open("manifest.json", "w") as f:
                json.dump(manifest, f, indent=2)

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