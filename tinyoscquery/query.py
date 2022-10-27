from zeroconf import ServiceBrowser, ServiceListener, Zeroconf


class OSCQueryListener(ServiceListener):

    def __init__(self) -> None:
        self.osc_services = {}
        self.oscjson_services = {}

        super().__init__()

    def remove_service(self, zc: 'Zeroconf', type_: str, name: str) -> None:
        if name in self.osc_services:
            del self.osc_services[name]

        if name in self.oscjson_services:
            del self.oscjson_services[name]

    def add_service(self, zc: 'Zeroconf', type_: str, name: str) -> None:
        if type_ == '_osc._udp.local.':
            self.osc_services[name] = zc.get_service_info(type_, name)
        elif type_ == '_oscjson._tcp.local.':
            self.oscjson_services[name] = zc.get_service_info(type_, name)


class OSCQueryBrowser(object):
    def __init__(self) -> None:
        self.listener = OSCQueryListener()
        self.zc = Zeroconf()
        self.browser = ServiceBrowser(self.zc, ["_oscjson._tcp.local.", "_osc._udp.local."], self.listener)

    def get_discovered_osc(self):
        return [oscsvc[1] for oscsvc in self.listener.osc_services.items()]

    def get_discovered_json(self):
        return [oscjssvc[1] for oscjssvc in self.listener.oscjson_services.items()]
