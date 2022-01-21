from server_func import server_func
import sys

if __name__ == '__main__':
    

    if len(sys.argv) != 3:
        print(f"Please type in: {sys.argv[0].split('/')[-1]} <host> <port>")
        exit(-1)
    
    try: 
        port = int(sys.argv[2])
        host = sys.argv[1]
    except ValueError:
        raise ValueError('port values should be integer')
    
    while True:
        server = server_func(host,port)
        try:
            server.setup()
            server.handle_rtsp_requests()
        except ConnectionError as e:
            server.server_state = 4
            print(f"Connection reset: {e}")
