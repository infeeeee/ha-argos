#!/usr/bin/env python3

import sys
from requests import post

# Read first 3 args:
SERVER_TOKEN = sys.argv[1]
SERVER_URL = sys.argv[2]
service = sys.argv[3].replace(".","/")

# Build url, token and header:
the_url = '/'.join([SERVER_URL, 'api', 'services', service])
the_token = ' '.join(['Bearer', SERVER_TOKEN])
headers = {
    "Authorization": the_token
}

# Parse the other arguments:
arguments = sys.argv[4:]
data = {}

if arguments:
    for arg in arguments:
        if arg.startswith('data:'):
            arg = arg[5:]
        argtuple = arg.split(sep=':', maxsplit=1)
        data[argtuple[0]]=argtuple[1]

# Call the server:
response = post(the_url, headers=headers, json=data)
print(response)