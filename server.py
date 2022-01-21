from server.server import Server
import sys

if __name__ == '__main__':
    

    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0].split('/')[-1]} <host> <port>")
        exit(-1)
    port = int(sys.argv[2])
    host = sys.argv[1]
    while True:
        server = Server(host,port)
        try:
            server.setup()
            server.handle_rtsp_requests()
        except ConnectionError as e:
            server.server_state = 4
            print(f"Connection reset: {e}")
