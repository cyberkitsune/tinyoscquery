# tinyoscquery
A very simple, work in progress, OSCQuery library for python.

**THIS IS VERY MUCH A WORK IN PROGRESS** Very little of OSCQuery is actually implemented right now, just the bare minimum to advertise that a server exists.

## Installation
1. Clone this repo
2. Run `pip install ./` in this repo folder

## Usage
To register a OSCQuery Service, simply construct a `OSCQueryService` (in `tinyoscquery.queryservice`) object with a name, and desired port numbers. The HTTP oscjson server and zeroconf advertisements will automataically start.

```Python
from tinyoscquery.queryservice import OSCQueryService
import time

osc_port = 9020 # Find a predefined open port for OSC
http_port = 9020 # Find a predefined open port for the oscjson http server -- can be the same port as osc

# Set up an OSCServer, likely with the python-osc first...

oscqs = OSCQueryService("Test-Service", http_port, osc_port)

# Do something else, the zeroconf advertising and oscjson server runs in the background
while True:
    time.sleep(1)

```

If you want to select any open ports on the system to use, a port finder is provided in the `tinyoscquery.utility` package.

```Python
from tinyoscquery.queryservice import OSCQueryService
from tinyoscquery.utility import get_open_tcp_port, get_open_udp_port
import time

osc_port = get_open_udp_port() # Find a random open port for OSC
http_port = get_open_tcp_port() # Find a random open port for the oscjson http server -- can be the same port as osc

# Set up an OSCServer, likely with the python-osc first...

oscqs = OSCQueryService("Test-Service", http_port, osc_port)

# Do something else, the zeroconf advertising and oscjson server runs in the background
while True:
    time.sleep(1)

```

## Project To-Do
- [x] Advertise osc and oscjson on zeroconfig
- [x] Provide a basic oscjson server with a root node and HOST_INFO
- [ ] Add a mechanism to advertise OSC nodes
- [ ] Add a mechanism to update OSC nodes with new values
- [ ] Add apis and tools to query other OSC services on the network