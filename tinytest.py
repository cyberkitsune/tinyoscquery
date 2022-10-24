import tinyoscquery, time

from tinyoscquery.queryservice import OSCQueryService

if __name__ == "__main__":
    oscqs = OSCQueryService("Test-Service", 9020, 9020)
    for path, node in oscqs.nodes.items():
        print(path, node)

    while True:
        time.sleep(1)