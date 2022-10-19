from zeroconf import ServiceInfo, Zeroconf
import time

class OSCQueryService(object):
    def __init__(self, serverName, httpPort, oscPort) -> None:
        self.serverName = serverName
        self.httpPort = httpPort
        self.oscPort = oscPort

        self._zeroconf = Zeroconf()
        self._startOSCQueryService()
        self._advertiseOSCService()


    def _startOSCQueryService(self):
        oscqsDesc = {'txtvers': 1}
        oscqsInfo = ServiceInfo("_oscjson._tcp.local.", "%s._oscjson._tcp.local." % self.serverName, self.httpPort, 
        0, 0, oscqsDesc, "%s.oscjson.local." % self.serverName, addresses=["127.0.0.1"])

        self._zeroconf.register_service(oscqsInfo)

    def _advertiseOSCService(self):
        oscDesc = {'txtvers': 1}
        oscInfo = ServiceInfo("_osc._udp.local.", "%s._osc._udp.local." % self.serverName, self.oscPort, 
        0, 0, oscDesc, "%s.osc.local." % self.serverName, addresses=["127.0.0.1"])

        self._zeroconf.register_service(oscInfo)


if __name__ == "__main__":
    oscqs = OSCQueryService("Test-Service", 9020, 9020)
    while True:
        time.sleep(1)
