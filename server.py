from server.server import Server


if __name__ == '__main__':
    import sys

    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0].split('/')[-1]} <host> <port>")
        exit(-1)
    try:
        port = int(sys.argv[2])
        host = sys.argv[1]
    except ValueError:
        raise ValueError('port value should be integer')

    while True:
        server = Server(host,port)
        try:
            server.setup()
            server.handle_rtsp_requests()
        except ConnectionError as e:
            server.server_state = server.STATE.TEARDOWN
            print(f"Connection reset: {e}")
