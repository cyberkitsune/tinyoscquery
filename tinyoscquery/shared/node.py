from enum import IntEnum
import json
from json import JSONEncoder

class OSCNodeEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, OSCQueryNode):
            obj_dict = {}
            for k, v in vars(o).items():
                if v is None:
                    continue
                if k.lower() == "type_":
                    obj_dict["TYPE"] = Python_Type_List_to_OSC_Type(v)
                if k == "contents":
                    obj_dict["CONTENTS"] = {}
                    for subNode in v:
                        if subNode.full_path is not None:
                            obj_dict["CONTENTS"][subNode.full_path.split("/")[-1]] = subNode
                        else:
                            continue
                else:
                    obj_dict[k.upper()] = v

            # FIXME: I missed something, so here's a hack!
            
            if "TYPE_" in obj_dict:
                del obj_dict["TYPE_"]
            return obj_dict

        if isinstance(o, type):
            return Python_Type_List_to_OSC_Type([o])
        
        return json.JSONEncoder.default(self, o)

class OSCAccess(IntEnum):
    NO_VALUE = 0
    READONLY_VALUE = 1
    WRITEONLY_VALUE = 2
    READWRITE_VALUE = 3

class OSCQueryNode():
    def __init__(self, full_path=None, contents=None, type_=None, access=None, description=None, value=None):
        self.contents = contents
        self.full_path = full_path
        self.access = access
        self.type_ = type_
        self.value = value
        self.description = description


    def find_subnode(self, full_path):
        if self.full_path == full_path:
            return self

        foundNode = None
        for subNode in self.contents:
            foundNode = subNode.find_subnode(full_path)
            if foundNode is not None:
                break

        return foundNode


    def __str__(self) -> str:
        return json.dumps(self, cls=OSCNodeEncoder)



def OSC_Type_String_to_Python_Type(typestr):
    types = []
    split = typestr.split()
    for typevalue in split:
        if typevalue == "i":
            types.append(int)
        elif typevalue == "f" or typevalue == "h" or typevalue == "d" or typevalue == "t":
            types.append(float)
        elif typevalue == "T" or typevalue == "F":
            types.append(bool)
        else:
            types.append(str)


    return types


def Python_Type_List_to_OSC_Type(types_):
    output = []
    for type_ in types_:
        if isinstance(type_, int):
            output.append("i")
        elif isinstance(type_, float):
            output.append("f")
        elif isinstance(type_, bool):
            output.append("T")
        else:
            output.append("s")

    return " ".join(output)
