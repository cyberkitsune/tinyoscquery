from zeroconf import ServiceInfo, Zeroconf
from http.server import SimpleHTTPRequestHandler, HTTPServer
import json, threading


class OSCQueryService(object):
    """
    A class providing an OSCQuery service. Automatically sets up a oscjson http server and advertises the oscjson server and osc server on zeroconf.

    Attributes
    ----------
    serverName : str
        Name of your OSC Service
    httpPort : int
        Desired TCP port number for the oscjson HTTP server
    oscPort : int
        Desired UDP port number for the osc server
    """
    
    def __init__(self, serverName, httpPort, oscPort, oscIp="127.0.0.1") -> None:
        self.serverName = serverName
        self.httpPort = httpPort
        self.oscPort = oscPort
        self.oscIp = oscIp

        self.nodes = {}

        def_exts = {"ACCESS": True, "CLIPMODE": False, "RANGE": True, "TYPE": True, "VALUE": True}

        self.add_node(OSCHostInfoNode(self.serverName, def_exts, self.oscIp, self.oscPort, "UDP"))
        self.add_node(OSCRootNode({}))

        self._zeroconf = Zeroconf()
        self._startOSCQueryService()
        self._advertiseOSCService()
        self.http_server = OSCQueryHTTPServer(self.nodes, ('', self.httpPort), OSCQueryHTTPHandler)
        self.http_thread = threading.Thread(target=self._startHTTPServer)
        self.http_thread.start()

    def add_node(self, node):
        path = node.get_path()
        if path is None:
            raise Exception("Tried to add node without a path!")

        self.nodes[path] = node

    def _startOSCQueryService(self):
        oscqsDesc = {'txtvers': 1}
        oscqsInfo = ServiceInfo("_oscjson._tcp.local.", "%s._oscjson._tcp.local." % self.serverName, self.httpPort, 
        0, 0, oscqsDesc, "%s.oscjson.local." % self.serverName, addresses=["127.0.0.1"])
        self._zeroconf.register_service(oscqsInfo)


    def _startHTTPServer(self):
        self.http_server.serve_forever()


    def _handleRoot(self):
        pass

    def _advertiseOSCService(self):
        oscDesc = {'txtvers': 1}
        oscInfo = ServiceInfo("_osc._udp.local.", "%s._osc._udp.local." % self.serverName, self.oscPort, 
        0, 0, oscDesc, "%s.osc.local." % self.serverName, addresses=["127.0.0.1"])

        self._zeroconf.register_service(oscInfo)

class OSCQueryHTTPServer(HTTPServer):
    def __init__(self, nodes, server_address: tuple[str, int], RequestHandlerClass, bind_and_activate: bool = ...) -> None:
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)
        self.nodes = nodes

class OSCQueryHTTPHandler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path in self.server.nodes:
            self.send_response(200)
            self.send_header("Content-type", "text/json")
            self.end_headers()
            self.wfile.write(bytes(str(self.server.nodes[self.path]), 'utf-8'))
        else:
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes("OSC Path not found", 'utf-8'))



class OSCQueryNode(object):
    def __init__(self, access=None, description=None) -> None:
        if description is not None:
            self.description = description
        if access is not None:
            self.access = access


    def __str__(self) -> str:
        return json.dumps(dict((k.upper(), v) for k, v in vars(self).items()))


    def get_path(self):
        return None


class OSCRootNode(OSCQueryNode):
    def __init__(self, contents) -> None:
        super().__init__("root node", 0)
        self.contents = contents

    
    def get_path(self):
        return "/"


class OSCPathNode(OSCQueryNode):
    def __init__(self, full_path, access, description=None, type=None, value=None, contents=None) -> None:
        super().__init__(description, access)
        self.full_path = full_path
        if type is not None:
            self.type = type
        
        if value is not None:
            self.value = value

        if contents is not None:
            self.contents = contents


    def get_path(self):
        return self.full_path


class OSCHostInfoNode(OSCQueryNode):
    def __init__(self, name, extensions, osc_ip, osc_port, osc_transport) -> None:
        self.name = name
        self.extensions = extensions
        self.osc_ip = osc_ip
        self.osc_port = osc_port
        self.osc_transport = osc_transport

    def get_path(self):
        return "/HOST_INFO"
