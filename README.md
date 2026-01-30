# tinyoscquery

A very simple, work-in-progress OSCQuery library for Python.

**Built on the original [cyberkitsune/tinyoscquery](https://github.com/cyberkitsune/tinyoscquery).** This fork adds same-port HTTP+WebSocket (per the [OSCQuery proposal](https://github.com/Vidvox/OSCQueryProposal)), LISTEN/IGNORE support, and binary OSC streaming for live value updates.

**THIS IS VERY MUCH A WORK IN PROGRESS** — only a subset of OSCQuery is implemented (advertising, HTTP oscjson, optional WebSocket streaming).

## Installation
1. Clone this repo
2. Run `pip install ./` in this repo folder

## Usage
### Advertising an OSCQuery Service
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
### Discovering and Querying other OSCQuery Services

To find other OSCQuery Services and read host info, utilize the `tinyoscquery.query` package to make a `OSCQueryBrowser` instance, wait for discovery, and then use `OSCQueryClient` to evaluate the HOST_INFO.
```python
import time

from tinyoscquery.query import OSCQueryBrowser, OSCQueryClient

browser = OSCQueryBrowser()
time.sleep(2) # Wait for discovery

for service_info in browser.get_discovered_oscquery():
    client = OSCQueryClient(service_info)

    # Find host info
    host_info = client.get_host_info()
    print(f"Found OSC Host: {host_info.name} with ip {host_info.osc_ip}:{host_info.osc_port}")

    # Query a node and print its value
    node = client.query_node("/test/node")
    print(f"Node is a {node.type_} with value {node.value}")
```



## Updating node values

After advertising endpoints, you can update their values so that HTTP GET requests return the latest value:

```python
from tinyoscquery.queryservice import OSCQueryService

oscqs = OSCQueryService("Test-Service", 9020, 9020)
oscqs.advertise_endpoint("/control/knob1", 0)
oscqs.advertise_endpoint("/control/knob2", 0)

# Update by path (value is visible on next HTTP query)
oscqs.update_value("/control/knob1", 255)
oscqs.update_value("/control/knob2", 128)

# Or get the node and mutate (same effect for HTTP)
node = oscqs.get_node("/control/knob1")
if node is not None:
    node.value[0] = 100
```

- **`get_node(path)`** — Returns the `OSCQueryNode` at `path`, or `None`. You can then set `node.value[0] = x` (or `node.value = [x]`).
- **`update_value(path, value)`** — Finds the node at `path`, sets its value (single value or list). Returns `True` if the node was found and updated.
- **WebSocket (live value updates)** — If `aiohttp` is installed, HTTP and WebSocket run on the **same port** (OSCQuery spec). HOST_INFO includes `ws_ip` and `ws_port` (same as HTTP). Clients connect to `ws://host:httpPort/`, send `{"COMMAND": "LISTEN", "DATA": "/path"}` to subscribe, and receive **binary OSC** packets when `update_value(path, value)` is called. If `aiohttp` is not installed but `websockets` is, a separate WebSocket server runs on `wsPort` (default `httpPort + 1`) and pushes JSON `{"path": path, "VALUE": value}` to all connected clients.
- **`set_push_target(host, port)`** — When set, each `update_value(path, value)` also sends an OSC message to `host:port`. Requires `pip install python-osc`. Pass `None, None` to disable.

## Project To-Do
- [x] Advertise osc and oscjson on zeroconfig
- [x] Provide a basic oscjson server with a root node and HOST_INFO
- [X] Add a mechanism to advertise OSC nodes
- [x] Add a mechanism to update OSC nodes with new values
- [X] Add apis and tools to query other OSC services on the network
- [ ] Add more documentation
- [ ] Finalize API design