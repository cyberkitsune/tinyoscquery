import json
import time
from itsdangerous import NoneAlgorithm
from zeroconf import ServiceBrowser, ServiceInfo, ServiceListener, Zeroconf
import requests

from shared.node import OSCQueryNode, OSC_Type_String_to_Python_Type, OSCAccess

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


class OSCQueryClient(object):
    def __init__(self, service_info) -> None:
        if not isinstance(service_info, ServiceInfo):
            raise Exception("service_info isn't a ServiceInfo class!")

        if service_info.type != "_oscjson._tcp.local.":
            raise Exception("service_info does not represent an OSCQuery service!")

        self.service_info = service_info
        self.last_json = None

    def _get_query_root(self):
        ip_str = '.'.join([str(int(num)) for num in self.service_info.addresses[0]])
        return f"http://{ip_str}:{self.service_info.port}"


    def query_node(self, node="/"):
        url = self._get_query_root() + node
        r = requests.get(url)
        if r.status_code != 200:
            raise Exception("Node query error: (HTTP", r.status_code, ") ", r.content)

        self.last_json = r.json()

        return self._make_node_from_json(self.last_json)

    def _make_node_from_json(self, json):
        newNode = OSCQueryNode()

        if "CONTENTS" in json:
            subNodes = []
            for subNode in json["CONTENTS"]:
                subNodes.append(self._make_node_from_json(json["CONTENTS"][subNode]))
            newNode.contents = subNodes

        # This *should* be required but some implementations don't have it...
        if "FULL_PATH" in json:
            newNode.full_path = json["FULL_PATH"]

    
        if "TYPE" in json:
            newNode.type_ = OSC_Type_String_to_Python_Type(json["TYPE"])

        # TODO: HOST_INFO

        if "DESCRIPTION" in json:
            newNode.description = json["DESCRIPTION"]

        if "ACCESS" in json:
            newNode.access = OSCAccess(json["ACCESS"])

        if "VALUE" in json:
            newNode.value = newNode.type_[0](json["VALUE"])


        return newNode




if __name__ == "__main__":
    fake_si = ServiceInfo("_oscjson._tcp.local.", "Test._oscjson._tcp.local.")
    queryclient = OSCQueryClient(fake_si)
    testcase_str = '{"DESCRIPTION":"root node","ACCESS":0,"CONTENTS":{"input":{"FULL_PATH":"/input","ACCESS":0,"CONTENTS":{"MoveForward":{"DESCRIPTION":"","FULL_PATH":"/input/MoveForward","ACCESS":3,"TYPE":"T"},"MoveBackward":{"DESCRIPTION":"","FULL_PATH":"/input/MoveBackward","ACCESS":3,"TYPE":"T"},"MoveLeft":{"DESCRIPTION":"","FULL_PATH":"/input/MoveLeft","ACCESS":3,"TYPE":"T"},"MoveRight":{"DESCRIPTION":"","FULL_PATH":"/input/MoveRight","ACCESS":3,"TYPE":"T"},"LookLeft":{"DESCRIPTION":"","FULL_PATH":"/input/LookLeft","ACCESS":3,"TYPE":"T"},"LookRight":{"DESCRIPTION":"","FULL_PATH":"/input/LookRight","ACCESS":3,"TYPE":"T"},"LookDown":{"DESCRIPTION":"","FULL_PATH":"/input/LookDown","ACCESS":3,"TYPE":"T"},"LookUp":{"DESCRIPTION":"","FULL_PATH":"/input/LookUp","ACCESS":3,"TYPE":"T"},"Jump":{"DESCRIPTION":"","FULL_PATH":"/input/Jump","ACCESS":3,"TYPE":"T"},"Run":{"DESCRIPTION":"","FULL_PATH":"/input/Run","ACCESS":3,"TYPE":"T"},"Back":{"DESCRIPTION":"","FULL_PATH":"/input/Back","ACCESS":3,"TYPE":"T"},"Menu":{"DESCRIPTION":"","FULL_PATH":"/input/Menu","ACCESS":3,"TYPE":"T"},"Menu2":{"DESCRIPTION":"","FULL_PATH":"/input/Menu2","ACCESS":3,"TYPE":"T"},"Reset Orientation":{"DESCRIPTION":"","FULL_PATH":"/input/Reset Orientation","ACCESS":3,"TYPE":"T"},"ComfortLeft":{"DESCRIPTION":"","FULL_PATH":"/input/ComfortLeft","ACCESS":3,"TYPE":"T"},"ComfortRight":{"DESCRIPTION":"","FULL_PATH":"/input/ComfortRight","ACCESS":3,"TYPE":"T"},"DropRight":{"DESCRIPTION":"","FULL_PATH":"/input/DropRight","ACCESS":3,"TYPE":"T"},"UseRight":{"DESCRIPTION":"","FULL_PATH":"/input/UseRight","ACCESS":3,"TYPE":"T"},"GrabRight":{"DESCRIPTION":"","FULL_PATH":"/input/GrabRight","ACCESS":3,"TYPE":"T"},"GrabUIRight":{"DESCRIPTION":"","FULL_PATH":"/input/GrabUIRight","ACCESS":3,"TYPE":"T"},"DropLeft":{"DESCRIPTION":"","FULL_PATH":"/input/DropLeft","ACCESS":3,"TYPE":"T"},"UseLeft":{"DESCRIPTION":"","FULL_PATH":"/input/UseLeft","ACCESS":3,"TYPE":"T"},"GrabLeft":{"DESCRIPTION":"","FULL_PATH":"/input/GrabLeft","ACCESS":3,"TYPE":"T"},"GrabUILeft":{"DESCRIPTION":"","FULL_PATH":"/input/GrabUILeft","ACCESS":3,"TYPE":"T"},"PanicButton":{"DESCRIPTION":"","FULL_PATH":"/input/PanicButton","ACCESS":3,"TYPE":"T"},"QuickMenuToggleLeft":{"DESCRIPTION":"","FULL_PATH":"/input/QuickMenuToggleLeft","ACCESS":3,"TYPE":"T"},"QuickMenuToggleRight":{"DESCRIPTION":"","FULL_PATH":"/input/QuickMenuToggleRight","ACCESS":3,"TYPE":"T"},"ToggleSitStand":{"DESCRIPTION":"","FULL_PATH":"/input/ToggleSitStand","ACCESS":3,"TYPE":"T"},"AFKToggle":{"DESCRIPTION":"","FULL_PATH":"/input/AFKToggle","ACCESS":3,"TYPE":"T"},"Voice":{"DESCRIPTION":"","FULL_PATH":"/input/Voice","ACCESS":3,"TYPE":"T"},"ShowDebugInfo0":{"DESCRIPTION":"","FULL_PATH":"/input/ShowDebugInfo0","ACCESS":3,"TYPE":"T"},"ShowDebugInfo1":{"DESCRIPTION":"","FULL_PATH":"/input/ShowDebugInfo1","ACCESS":3,"TYPE":"T"},"ShowDebugInfo2":{"DESCRIPTION":"","FULL_PATH":"/input/ShowDebugInfo2","ACCESS":3,"TYPE":"T"},"ShowDebugInfo3":{"DESCRIPTION":"","FULL_PATH":"/input/ShowDebugInfo3","ACCESS":3,"TYPE":"T"},"ShowDebugInfo4":{"DESCRIPTION":"","FULL_PATH":"/input/ShowDebugInfo4","ACCESS":3,"TYPE":"T"},"ShowDebugInfo5":{"DESCRIPTION":"","FULL_PATH":"/input/ShowDebugInfo5","ACCESS":3,"TYPE":"T"},"ShowDebugInfo6":{"DESCRIPTION":"","FULL_PATH":"/input/ShowDebugInfo6","ACCESS":3,"TYPE":"T"},"ShowDebugInfo7":{"DESCRIPTION":"","FULL_PATH":"/input/ShowDebugInfo7","ACCESS":3,"TYPE":"T"},"ShowDebugInfo8":{"DESCRIPTION":"","FULL_PATH":"/input/ShowDebugInfo8","ACCESS":3,"TYPE":"T"},"ShowDebugInfo9":{"DESCRIPTION":"","FULL_PATH":"/input/ShowDebugInfo9","ACCESS":3,"TYPE":"T"},"Vertical":{"DESCRIPTION":"","FULL_PATH":"/input/Vertical","ACCESS":3,"TYPE":"f"},"Horizontal":{"DESCRIPTION":"","FULL_PATH":"/input/Horizontal","ACCESS":3,"TYPE":"f"},"LookHorizontal":{"DESCRIPTION":"","FULL_PATH":"/input/LookHorizontal","ACCESS":3,"TYPE":"f"},"LookVertical":{"DESCRIPTION":"","FULL_PATH":"/input/LookVertical","ACCESS":3,"TYPE":"f"},"UseAxisRight":{"DESCRIPTION":"","FULL_PATH":"/input/UseAxisRight","ACCESS":3,"TYPE":"f"},"GrabAxisRight":{"DESCRIPTION":"","FULL_PATH":"/input/GrabAxisRight","ACCESS":3,"TYPE":"f"},"MoveHoldFB":{"DESCRIPTION":"","FULL_PATH":"/input/MoveHoldFB","ACCESS":3,"TYPE":"f"},"SpinHoldCwCcw":{"DESCRIPTION":"","FULL_PATH":"/input/SpinHoldCwCcw","ACCESS":3,"TYPE":"f"},"SpinHoldUD":{"DESCRIPTION":"","FULL_PATH":"/input/SpinHoldUD","ACCESS":3,"TYPE":"f"},"SpinHoldLR":{"DESCRIPTION":"","FULL_PATH":"/input/SpinHoldLR","ACCESS":3,"TYPE":"f"}}}}}'
    queryclient.last_json = json.loads(testcase_str)
    node = queryclient._make_node_from_json(queryclient.last_json)
    print(node)

        
        