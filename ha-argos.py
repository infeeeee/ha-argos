#!/usr/bin/env python3

import os
import requests
import sys
import yaml
import json
from collections import defaultdict
import base64
from lxml import etree as ET

reload_string = '<span weight="bold">Reload</span> | refresh=true iconName=view-refresh-symbolic'

# --------------------------------- Functions -------------------------------- #


def call_ha(endpoint):
    """Call homeassistant

    Args:
        endpoint (String): the endpoint to call

    Returns:
        Dict: The answer from the server as a dictionary
    """
    the_url = '/'.join([SERVER_URL, 'api', endpoint])
    the_token = ' '.join(['Bearer', SERVER_TOKEN])
    headers = {
        "Authorization": the_token,
        "content-type": "application/json",
    }
    response = requests.get(the_url, headers=headers)
    return response.json()


def get_ha_attr(attr,  entity_dict, use_cache=False):
    """Get attribute values from config, cache or ha

    Args:
        attr (str or list): The attribute or the list of attributes
        entity_dict (dict): The entity dictionary read from config file
        use_cache (bool, optional): Use the cache for storing this attribute. Defaults to False.
    Returns:
        str: The attribute value
    """
    global CACHE_CHANGED

    if not isinstance(attr, list):
        # Return attribute value from config file:
        if entity_dict[attr]:
            return entity_dict[attr]

        # Return attribute value from the cache:
        if use_cache and CACHE[entity_dict['entity']]:
            if CACHE[entity_dict['entity']][attr]:
                return CACHE[entity_dict['entity']][attr]
    # Call ha for attribute:
    e_state = call_ha(f'states/{entity_dict["entity"]}')
    if isinstance(attr, list):
        e_vals = []
        for att in attr:
            if att == 'state':
                e_vals.append(str(e_state[att]))
            else:
                e_vals.append(str(e_state['attributes'][att]))
        # write to cache:
        if use_cache:
            CACHE_CHANGED = True
            for att in attr:
                if not att == 'state':
                    CACHE[entity_dict['entity']][att] \
                        = e_state['attributes'][att]
        return e_vals
    else:
        if use_cache and not attr == 'state':
            CACHE_CHANGED = True
            CACHE[entity_dict['entity']] = dict()
            CACHE[entity_dict['entity']][attr] = e_state['attributes'][attr]
        return e_state['attributes'][attr]


def print_line(line, submenu=False):
    """Print a line from the yaml config

    Args:
        line (dict): Data from configuration.yaml
        submenu (bool, optional): Print it to a submenu, for recursion. Defaults to False.
    """
    # It's a separator
    if isinstance(line, str) and line == 'separator':
        print('---')
        return

    cmd = defaultdict(bool, line)
    output = []

    # It's a list of other elements
    if cmd['entities']:
        # Add name or empty string to output
        if cmd['name']:
            output.append(cmd['name'])
        else:
            output.append(' ')

        # Add icon:
        if cmd['icon']:
            output.extend(['|', print_icon(cmd['icon'])])
        print((' ').join(output))

        # Recurse into lines:
        for e in cmd['entities']:
            print_line(e, True)
        return

    # Add prefix if called from a submenu:
    if submenu:
        output.append('--')

    # Add general prefix:
    if cmd['prefix']:
        output.append(cmd['prefix'])

    # There is a command or an atribute:
    if cmd['entity']:
        # Display attribute value from ha:
        if cmd['attribute']:
            c_val = get_ha_attr(cmd['attribute'], cmd)
            if isinstance(c_val, list):
                c_val = ' '.join(c_val)
            output.append(c_val)

        # If no attribute but a name given, print that:
        elif cmd['name']:
            output.append(cmd['name'])

        # No attribute, so display it's friendly_name from ha cache or from config:
        else:
            output.append(get_ha_attr('friendly_name', cmd, True))

    # Display the name if not an entity
    elif cmd['name']:
        output.extend([cmd['name']])

    # There is a call to a service:
    if cmd['service'] and cmd['entity']:
        output.append(
            f'| bash=\"curl -X POST -H \\"Authorization: Bearer {SERVER_TOKEN}\\" -H \\"Content-Type: application/json\\"'
        )
        if cmd['data']:
            output.append(
                f'-d \'{{\\"entity_id\\": \\"{cmd["entity"]}\\",')
            data_keys = [d for d in cmd['data']]
            for i, d in enumerate(data_keys):
                output.append(f'\\"{d}\\": \\"{cmd["data"][d]}\\"')
                if i != len(data_keys) - 1:
                    output.append(',')
            output.append('}\'')
        else:
            output.append(
                f'-d \'{{\\"entity_id\\": \\"{cmd["entity"]}\\"}}\''
            )
        output.append(
            f'{SERVER_URL}/api/services/{cmd["service"].replace(".","/")}" terminal=false'
        )
    # No call, so add a separator:
    else:
        output.append('|')

    # Add icon:
    if cmd['icon']:
        output.append(print_icon(cmd['icon']))

    print((' ').join(output))


def print_icon(icon_string):
    """Print an icon from cache, gtk or mdi

    Args:
        icon_string (String): The name of the icon

    Returns:
        String: The icon as string, base64 or gtk...
    """
    if icon_string.startswith('gtk:'):
        return f'iconName={icon_string[4:]}'
    elif icon_string.startswith('mdi:'):
        mdi_name = icon_string[4:]
        # Try to find it in cache:
        if CACHE[icon_string]:
            return append_icon_size(f'image={CACHE[icon_string]}')
        else:
            icon_resp = requests.get(
                f'https://raw.githubusercontent.com/Templarian/MaterialDesign-SVG/master/svg/{mdi_name}.svg')

            # Build svg tree:
            svg_root = ET.fromstring(icon_resp.content)

            # Change svg color:

            for t in svg_root:
                if SETTINGS["icon_color"] and t.tag == '{http://www.w3.org/2000/svg}path':
                    t.set('style', f'fill:#{SETTINGS["icon_color"]}')

            # svg to string:
            icon_str = ET.tostring(
                svg_root,
                encoding='utf-8',
                method='xml',
                xml_declaration=True
            )

            # Encode and cache svg
            icon_b = base64.b64encode(icon_str).decode("utf-8")
            global CACHE_CHANGED
            CACHE_CHANGED = True
            CACHE[icon_string] = icon_b
            return append_icon_size(f'image={icon_b}')
    else:
        return append_icon_size(f'image={icon_string}')


def append_icon_size(image_string):
    """Append icon size based on config

    Args:
        image_string (String): The icon as string

    Returns:
        String: The icon as string with size
    """
    if SETTINGS["icon_size"]:
        return f'{image_string}, imageWidth={SETTINGS["icon_size"]}'
    else:
        return image_string

# ------------------------------- Start script ------------------------------- #

HOST = 'argos'

# Check if Argos or Xbar:
if os.getenv('ARGOS_VERSION') != '2':
    HOST = 'xbar'
    

# -------------------------- Open configuration.yaml ------------------------- #


script_dir = os.path.dirname(os.path.realpath(__file__))

try:
    with open(os.path.join(script_dir, 'configuration.yaml'), 'r') as config_file:
        config = defaultdict(bool, yaml.safe_load(config_file))

except FileNotFoundError:
    print('No config!')
    print('---')
    print('Configuration.yaml not found. Please create one!')
    print('It should be in this directory:')
    print(script_dir)
    print('---')
    print(reload_string)
    exit()

# ------------------------------ Open cache file ----------------------------- #

try:
    with open(os.path.join(script_dir, 'cache.json'), 'r') as cache_file:
        json_dict = json.load(cache_file)
    CACHE = defaultdict(bool, json_dict)

except (FileNotFoundError, json.decoder.JSONDecodeError):
    CACHE = defaultdict(lambda: defaultdict(bool))


CACHE_CHANGED = False

# --------------------------- Check server settings -------------------------- #

if not config['settings']['url'] or not config['settings']['token']:
    print('No credentials!')
    print('---')
    print('Server url or token missing from cofiguration.yaml')
    print('---')
    print(reload_string)
    exit()

# Sanitize:
SERVER_URL = config['settings']['url']
if SERVER_URL[-1] == '/':
    SERVER_URL = SERVER_URL[:-1]
SERVER_TOKEN = config['settings']['token']
SETTINGS = defaultdict(bool, config['settings'])


# ----------------------------------- Lines ---------------------------------- #

if config['lines']:
    for l in config['lines']:
        print_line(l)
else:
    print('HA')


print('---')
print(reload_string)

# -------------------------------- Write cache ------------------------------- #

if CACHE_CHANGED:
    cache_json = json.dumps(CACHE)

    with open(os.path.join(script_dir, 'cache.json'), "w") as outfile:
        outfile.write(cache_json)
