import socket

def get_open_tcp_port():
    '''
    Returns a valid, open, TCP port.

        Returns:
            port (int): A TCP port that is able to be bound to
    '''
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port

def get_open_udp_port():
    '''
    Returns a valid, open, UDP port.

        Returns:
            port (int): A UDP port that is able to be bound to
    '''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port