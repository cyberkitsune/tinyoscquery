from zeroconf import ServiceInfo, Zeroconf
from http.server import SimpleHTTPRequestHandler, HTTPServer
from .shared.node import OSCQueryNode, OSCHostInfo, OSCAccess
import asyncio
import json
import threading

try:
    from pythonosc.udp_client import SimpleUDPClient
    from pythonosc.osc_message_builder import OscMessageBuilder
    _HAS_PYTHON_OSC = True
except ImportError:
    _HAS_PYTHON_OSC = False

try:
    import aiohttp
    from aiohttp import web
    _HAS_AIOHTTP = True
except ImportError:
    _HAS_AIOHTTP = False

try:
    import websockets
    _HAS_WEBSOCKETS = True
except ImportError:
    _HAS_WEBSOCKETS = False


def _osc_message_bytes(path, values):
    """Build raw OSC packet bytes for path and value list. Returns None if python-osc not available."""
    if not _HAS_PYTHON_OSC:
        return None
    try:
        builder = OscMessageBuilder(address=path)
        for v in values:
            builder.add_arg(v)
        msg = builder.build()
        return getattr(msg, "dgram", getattr(msg, "_dgram", None))
    except Exception:
        return None


class OSCQueryService(object):
    """
    A class providing an OSCQuery service. Automatically sets up a oscjson http server and advertises the oscjson server and osc server on zeroconf.

    If aiohttp is installed, HTTP and WebSocket run on the same port (OSCQuery spec: same IP/port).
    Otherwise falls back to threading HTTP server and optional WebSocket on a separate port.

    Attributes
    ----------
    serverName : str
        Name of your OSC Service
    httpPort : int
        Desired TCP port number for the oscjson HTTP server
    oscPort : int
        Desired UDP port number for the osc server
    """
    
    def __init__(self, serverName, httpPort, oscPort, oscIp="127.0.0.1", wsPort=None) -> None:
        self.serverName = serverName
        self.httpPort = httpPort
        self.oscPort = oscPort
        self.oscIp = oscIp
        # Same port as HTTP when using aiohttp (OSCQuery spec); else separate port
        self.wsPort = httpPort if _HAS_AIOHTTP else (wsPort if wsPort is not None else (httpPort + 1))
        self._push_host = None
        self._push_port = None
        self._osc_client = None
        self._ws_connections = set()
        self._ws_listen_paths = {}  # ws -> set of paths this client LISTENs to
        self._ws_loop = None
        self._ws_server = None
        self._use_aiohttp = _HAS_AIOHTTP

        extensions = {"ACCESS": True, "CLIPMODE": False, "RANGE": True, "TYPE": True, "VALUE": True}
        if _HAS_AIOHTTP:
            extensions["LISTEN"] = True
            extensions["PATH_CHANGED"] = True
        self.root_node = OSCQueryNode("/", description="root node")
        self.host_info = OSCHostInfo(
            serverName, extensions,
            self.oscIp, self.oscPort, "UDP", ws_ip=self.oscIp, ws_port=self.wsPort
        )

        self._zeroconf = Zeroconf()
        self._startOSCQueryService()
        self._advertiseOSCService()
        if _HAS_AIOHTTP:
            self.http_server = None
            self._aiohttp_runner = None
            self._aiohttp_site = None
            self._aiohttp_loop = asyncio.new_event_loop()
            self._aio_thread = threading.Thread(target=self._run_aiohttp_server, daemon=True)
            self._aio_thread.start()
        else:
            self.http_server = OSCQueryHTTPServer(self.root_node, self.host_info, ('', self.httpPort), OSCQueryHTTPHandler)
            self.http_thread = threading.Thread(target=self._startHTTPServer, daemon=True)
            self.http_thread.start()
        if _HAS_WEBSOCKETS and not _HAS_AIOHTTP:
            self._ws_thread = threading.Thread(target=self._run_ws_server, daemon=True)
            self._ws_thread.start()

    def __del__(self):
        self._zeroconf.unregister_all_services()

    def add_node(self, node):
        self.root_node.add_child_node(node)

    def get_node(self, path):
        """Return the OSCQueryNode at the given path, or None if not found."""
        path = path.split("?")[0] if path else path
        return self.root_node.find_subnode(path)

    def set_push_target(self, host, port):
        """
        Set the host:port to send OSC messages to when update_value() is called.
        Clients (e.g. Chataigne) can listen for OSC on this port to get live value updates.
        Pass None, None to disable push.
        """
        self._push_host = host
        self._push_port = port
        self._osc_client = None

    def update_value(self, path, value):
        """
        Update the value of the node at the given path.
        Value can be a single value or a list (for multi-argument nodes).
        Returns True if the node was found and updated, False otherwise.
        The updated value is immediately visible to HTTP GET requests.
        If set_push_target(host, port) was set and python-osc is installed, also sends an OSC message.
        If WebSocket (same port or separate) is in use, streams value to clients that LISTEN to this path (binary OSC when same port).
        """
        node = self.get_node(path)
        if node is None:
            return False
        if not isinstance(value, list):
            node.value = [value]
            osc_args = [value]
        else:
            node.value = list(value)
            osc_args = list(value)
        if self._push_host is not None and self._push_port is not None and _HAS_PYTHON_OSC:
            try:
                if self._osc_client is None:
                    self._osc_client = SimpleUDPClient(self._push_host, self._push_port)
                self._osc_client.send_message(path, osc_args[0] if len(osc_args) == 1 else osc_args)
            except Exception:
                pass
        if self._use_aiohttp and self._aiohttp_loop is not None and self._ws_connections:
            osc_bytes = _osc_message_bytes(path, node.value)
            if osc_bytes:
                asyncio.run_coroutine_threadsafe(
                    self._ws_broadcast_osc(path, osc_bytes), self._aiohttp_loop
                )
        elif _HAS_WEBSOCKETS and self._ws_loop is not None and self._ws_connections:
            try:
                msg = json.dumps({"path": path, "VALUE": node.value})
                asyncio.run_coroutine_threadsafe(self._ws_broadcast(msg), self._ws_loop)
            except Exception:
                pass
        return True

    async def _ws_broadcast_osc(self, path, osc_bytes):
        """Send binary OSC packet to every WebSocket client that LISTENs to this path."""
        disconnected = []
        for ws in list(self._ws_connections):
            paths = self._ws_listen_paths.get(ws)
            if paths and path in paths:
                try:
                    await ws.send_bytes(osc_bytes)
                except Exception:
                    disconnected.append(ws)
        for ws in disconnected:
            self._ws_connections.discard(ws)
            self._ws_listen_paths.pop(ws, None)

    async def _ws_broadcast(self, message):
        if not self._ws_connections:
            return
        disconnected = set()
        for ws in self._ws_connections:
            try:
                await ws.send(message)
            except Exception:
                disconnected.add(ws)
        for ws in disconnected:
            self._ws_connections.discard(ws)
            self._ws_listen_paths.pop(ws, None)

    def _run_aiohttp_server(self):
        if not _HAS_AIOHTTP:
            return
        app = web.Application()
        root_node = self.root_node
        host_info = self.host_info

        async def handle_get(request):
            path_str = request.path if request.path else "/"
            if path_str != "/":
                path_str = "/" + path_str.lstrip("/")  # ensure leading /
            if "HOST_INFO" in (request.query_string or ""):
                return web.json_response(json.loads(host_info.to_json()), headers={"Cache-Control": "no-store, no-cache, must-revalidate", "Pragma": "no-cache"})
            node = root_node.find_subnode(path_str)
            if node is None:
                return web.Response(text="OSC Path not found", status=404, content_type="text/json")
            return web.json_response(json.loads(node.to_json()), headers={"Cache-Control": "no-store, no-cache, must-revalidate", "Pragma": "no-cache"})

        async def handle_ws(request):
            ws = web.WebSocketResponse()
            await ws.prepare(request)
            self._ws_connections.add(ws)
            self._ws_listen_paths[ws] = set()
            try:
                async for msg in ws:
                    if msg.type == web.WSMsgType.TEXT:
                        try:
                            obj = json.loads(msg.data)
                            cmd = (obj.get("COMMAND") or "").strip().upper()
                            data = obj.get("DATA")
                            if cmd == "LISTEN" and isinstance(data, str):
                                self._ws_listen_paths[ws].add(data)
                            elif cmd == "IGNORE" and isinstance(data, str):
                                self._ws_listen_paths[ws].discard(data)
                        except (json.JSONDecodeError, TypeError):
                            pass
            finally:
                self._ws_connections.discard(ws)
                self._ws_listen_paths.pop(ws, None)
            return ws

        async def root_or_ws(request):
            if request.headers.get("Upgrade", "").lower() == "websocket":
                return await handle_ws(request)
            return await handle_get(request)

        app.router.add_get("/", root_or_ws)
        app.router.add_get("/{path:.*}", handle_get)

        async def start():
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, "", self.httpPort)
            await site.start()
            self._aiohttp_runner = runner
            self._aiohttp_site = site

        self._aiohttp_loop.run_until_complete(start())
        self._aiohttp_loop.run_forever()

    def _run_ws_server(self):
        if not _HAS_WEBSOCKETS:
            return
        async def handler(websocket):
            self._ws_connections.add(websocket)
            self._ws_listen_paths[websocket] = set()
            try:
                async for msg in websocket:
                    try:
                        raw = msg.data if isinstance(msg, object) and hasattr(msg, "data") else msg
                        if isinstance(raw, bytes):
                            raw = raw.decode("utf-8", errors="replace")
                        obj = json.loads(raw)
                        cmd = (obj.get("COMMAND") or "").strip().upper()
                        data = obj.get("DATA")
                        if cmd == "LISTEN" and isinstance(data, str):
                            self._ws_listen_paths[websocket].add(data)
                        elif cmd == "IGNORE" and isinstance(data, str):
                            self._ws_listen_paths[websocket].discard(data)
                    except (json.JSONDecodeError, TypeError):
                        pass
            finally:
                self._ws_connections.discard(websocket)
                self._ws_listen_paths.pop(websocket, None)
            await websocket.wait_closed()
        self._ws_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._ws_loop)
        self._ws_server = self._ws_loop.run_until_complete(
            websockets.serve(handler, "", self.wsPort, ping_interval=20, ping_timeout=20)
        )
        self._ws_loop.run_forever()

    def advertise_endpoint(self, address, value=None, access=OSCAccess.READWRITE_VALUE):
        new_node = OSCQueryNode(full_path=address, access=access)
        if value is not None:
            if not isinstance(value, list):
                new_node.value = [value]
                new_node.type_ = [type(value)]
            else:
                new_node.value = value
                new_node.type_ = [type(v) for v in value]
        self.add_node(new_node)

    def _startOSCQueryService(self):
        oscqsDesc = {'txtvers': 1}
        oscqsInfo = ServiceInfo("_oscjson._tcp.local.", "%s._oscjson._tcp.local." % self.serverName, self.httpPort, 
        0, 0, oscqsDesc, "%s.oscjson.local." % self.serverName, addresses=["127.0.0.1"])
        self._zeroconf.register_service(oscqsInfo)


    def _startHTTPServer(self):
        self.http_server.serve_forever()

    def _advertiseOSCService(self):
        oscDesc = {'txtvers': 1}
        oscInfo = ServiceInfo("_osc._udp.local.", "%s._osc._udp.local." % self.serverName, self.oscPort, 
        0, 0, oscDesc, "%s.osc.local." % self.serverName, addresses=["127.0.0.1"])

        self._zeroconf.register_service(oscInfo)


class OSCQueryHTTPServer(HTTPServer):
    def __init__(self, root_node, host_info, server_address: tuple[str, int], RequestHandlerClass, bind_and_activate: bool = ...) -> None:
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)
        self.root_node = root_node
        self.host_info = host_info


class OSCQueryHTTPHandler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        if 'HOST_INFO' in self.path:
            self.send_response(200)
            self.send_header("Content-type", "text/json")
            self.end_headers()
            self.wfile.write(bytes(str(self.server.host_info.to_json()), 'utf-8'))
            return
        # Strip query string so /ring/X?foo=bar still finds /ring/X
        request_path = self.path.split("?")[0]
        node = self.server.root_node.find_subnode(request_path)
        if node is None:
            self.send_response(404)
            self.send_header("Content-type", "text/json")
            self.end_headers()
            self.wfile.write(bytes("OSC Path not found", 'utf-8'))
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/json")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.end_headers()
            self.wfile.write(bytes(str(node.to_json()), 'utf-8'))

    def log_message(self, format, *args):
        pass
            
