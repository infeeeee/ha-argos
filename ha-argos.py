#!/usr/bin/env python3

# <bitbar.title>ha-argos</bitbar.title>
# <bitbar.version>v0.1</bitbar.version>
# <bitbar.author>infeeeee</bitbar.author>
# <bitbar.author.github>infeeeee</bitbar.author.github>
# <bitbar.desc> Put Home Asstisant in your top bar!</bitbar.desc>
# <bitbar.image>https://raw.githubusercontent.com/infeeeee/ha-argos/main/images/Screenshot%20from%202022-05-09%2023-54-36.png</bitbar.image>
# <bitbar.dependencies>python, homebrew</bitbar.dependencies>
# <bitbar.abouturl>https://github.com/infeeeee/ha-argos</bitbar.abouturl>

# <swiftbar.hideAbout>true</swiftbar.hideAbout>
# <swiftbar.hideRunInTerminal>true</swiftbar.hideRunInTerminal>
# <swiftbar.hideLastUpdated>true</swiftbar.hideLastUpdated>
# <swiftbar.hideDisablePlugin>true</swiftbar.hideDisablePlugin>
# <swiftbar.hideSwiftBar>true</swiftbar.hideSwiftBar>

# <xbar.title>ha-argos</xbar.title>
# <xbar.version>v0.1</xbar.version>
# <xbar.author>infeeeee</xbar.author>
# <xbar.author.github>infeeeee</xbar.author.github>
# <xbar.desc> Put Home Asstisant in your top bar!</xbar.desc>
# <xbar.image>https://raw.githubusercontent.com/infeeeee/ha-argos/main/images/Screenshot%20from%202022-05-09%2023-54-36.png</xbar.image>
# <xbar.dependencies>python, homebrew</xbar.dependencies>
# <xbar.abouturl>https://github.com/infeeeee/ha-argos</xbar.abouturl>

#  <xbar.var>string(HA_CONFIG_PATH="$HOME/Library/Application Support/xbar/plugins/ha-argos/configuration.yaml"): Path to configuartion.yaml</xbar.var>

import os
from requests import get
import sys
import yaml
import json
from collections import defaultdict
import base64
from lxml import etree as ET
from cairosvg import svg2png

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
    response = get(the_url, headers=headers)
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
                # Defaultdict, if the parameter doesn't exist:
                e_attrs = defaultdict(bool, e_state['attributes'])
                if e_attrs[att]:
                    e_vals.append(str(e_attrs[att]))
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
                if cmd['attribute_separator']:
                    c_val = cmd['attribute_separator'].join(c_val)
                else:
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
    if cmd['service']:
        bash_word = 'bash'
        if HOST == 'xbar':
            bash_word = 'shell'
        output.extend([
            f'| {bash_word}={SCRIPT_DIR}/ha-service.py param1="{SERVER_TOKEN}"',
            f'param2="{SERVER_URL}"',
            f'param3="{cmd["service"]}"'
        ])
        pn = 4
        if cmd['entity'] or cmd['data']:
            if cmd['entity']:
                output.append(
                    f'param{pn}="entity_id:{cmd["entity"]}"'
                )
                pn += 1
            if cmd['data']:
                data_keys = [d for d in cmd['data']]
                for i, d in enumerate(data_keys):
                    output.append(f'param{pn}="data:{d}:{cmd["data"][d]}"')
                    pn += 1
        output.append('terminal=false')

    # Add icon:
    if cmd['icon']:
        output.append('|')
        output.append(print_icon(cmd['icon']))

    print((' ').join(output))


def print_icon(icon_string):
    """Print an icon from cache, gtk or mdi

    Args:
        icon_string (String): The name of the icon

    Returns:
        String: The icon as string, base64 or gtk...
    """
    if NOIMAGE:
        return ''
    if icon_string.startswith('gtk:') and HOST == 'argos':
        return f'iconName={icon_string[4:]}'
    elif icon_string.startswith('mdi:'):
        mdi_name = icon_string[4:]
        # Try to find it in cache:
        if CACHE[icon_string] and not NOCACHE:
            return append_icon_size(f'templateImage={CACHE[icon_string]}')

        # Download icon if not in the cache:
        else:
            icon_resp = get(
                f'https://raw.githubusercontent.com/Templarian/MaterialDesign-SVG/master/svg/{mdi_name}.svg')

            if HOST == 'argos':
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

                # Encode svg:
                icon_b = base64.b64encode(icon_str).decode("utf-8")

            elif HOST == 'xbar' or HOST == 'swiftbar':
                # Convert to png on mac:
                icon_png = svg2png(
                    bytestring=icon_resp.content,
                    dpi=144
                )
                # Encode png:
                icon_b = base64.b64encode(icon_png).decode("utf-8")

            # Cache:
            if not NOCACHE:
                global CACHE_CHANGED
                CACHE_CHANGED = True
                CACHE[icon_string] = icon_b

            return append_icon_size(f'templateImage={icon_b}')
    else:
        # The other option should a base64 ecoded image:
        return append_icon_size(f'templateImage={icon_string}')


def append_icon_size(image_string):
    """Append icon size based on config

    Args:
        image_string (String): The icon as string

    Returns:
        String: The icon as string with size
    """
    if SETTINGS["icon_size"] and HOST == 'argos':
        return f'{image_string}, imageWidth={SETTINGS["icon_size"]}'
    else:
        return image_string

# ------------------------------- Start script ------------------------------- #


# Check host:
HOST = ''
if os.getenv('ARGOS_VERSION') == '2':
    HOST = 'argos'
elif os.getenv('XBARDarkMode'):
    HOST = 'xbar'
if os.getenv('SWIFTBAR') == '1':
    HOST = 'swiftbar'

# Do not print images for easier debugging:
NOIMAGE = False

# Usage: ./ha-argos.py --noimage
if '--noimage' in sys.argv:
    NOIMAGE = True

# Do not use cache
NOCACHE = False

# Usage: ./ha-argos.py --noimage
if '--nocache' in sys.argv:
    NOCACHE = True

# -------------------------- Open configuration.yaml ------------------------- #


SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

try:
    # Try to find configuration.yaml:
    config_path = os.path.join(SCRIPT_DIR, 'configuration.yaml')
    if HOST == 'xbar' and os.getenv('HA_CONFIG_PATH'):
        config_path = os.getenv('HA_CONFIG_PATH')

    with open(config_path, 'r') as config_file:
        config = defaultdict(bool, yaml.safe_load(config_file))

except FileNotFoundError:
    print('No config!')
    print('---')
    print('Configuration.yaml not found. Please create one!')
    print('It should be in this directory:')
    print(f'{SCRIPT_DIR} | href={SCRIPT_DIR}')
    if HOST == 'argos':
        print('---')
        print(reload_string)
    exit()

# ------------------------------ Open cache file ----------------------------- #

try:
    with open(os.path.join(SCRIPT_DIR, 'cache.json'), 'r') as cache_file:
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

if HOST == 'argos':
    print('---')
    print(reload_string)

# -------------------------------- Write cache ------------------------------- #

if CACHE_CHANGED:
    cache_json = json.dumps(CACHE)

    with open(os.path.join(SCRIPT_DIR, 'cache.json'), "w") as outfile:
        outfile.write(cache_json)
