from enum import Enum

class OSCAccess(Enum):
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