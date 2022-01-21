import socket
from time import sleep
from threading import Thread
from video_stream import videostream
from rtsp import rtsp
from rtp import rtp


# state:init = 0, puase = 1, play = 2, video finish = 3, teardown = 4

class server_func:

    period = 1000//30
    id = '666666'
    HOST = '127.0.0.1'

    def __init__(self, host,rtsp_port):
        self.stream = None
        self.rtp_thread = None
        self.rtsp_connection = None
        self.rtp_socket = None
        self.client_address = None
        self.server_state = 0
        self.live = True
        self.HOST = host

        self.rtsp_port = rtsp_port

    def rtsp_packet(self):
        recv = ''
        while True:
            try:
                recv = self.rtsp_connection.recv(4096)
                break
            except socket.timeout:
                continue
        print(f"Received from client: {repr(recv)}")
        return rtsp.from_request(recv)

    def setup(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        address = self.HOST, self.rtsp_port
        s.bind(address)
        print(f"Listening on {address[0]}:{address[1]}...")
        s.listen(5)
        print("Waiting for connection...")
        self.rtsp_connection, self.client_address = s.accept()
        self.rtsp_connection.settimeout(0.1)
        print(f"Accepted connection from {self.client_address[0]}:{self.client_address[1]}")

        if self.server_state != 0:
            raise Exception('server is already setup')
        while True:
            packet = self.rtsp_packet()
            if packet.request_type == rtsp.SETUP:
                self.server_state = 1
                print('State set to PAUSED')
                self.client_address = self.client_address[0], packet.rtp_dst_port
                self.stream = videostream(packet.video_file_path)
                self.rtp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.rtp_thread = Thread(target=self.video_send, daemon=True)
                self.rtp_thread.start()
                self.send_rtsp_response(packet.sequence_number)
                break


    def handle_rtsp_requests(self):
        while True:
            packet = self.rtsp_packet()
            if packet.request_type == rtsp.PLAY:
                if self.server_state == 2:
                    print('Current state is already PLAYING.')
                    continue
                self.server_state = 2
                print('State set to PLAYING.')
            elif packet.request_type == rtsp.PAUSE:
                if self.server_state == 1:
                    print('Current state is already PAUSED.')
                    continue
                self.server_state = 1
                print('State set to PAUSED.')
            else:
                self.send_rtsp_response(packet.sequence_number)
                self.rtsp_connection.close()
                self.stream.close()
                self.rtp_socket.close()
                self.server_state = 4
                raise ConnectionError('teardown requested')
            self.send_rtsp_response(packet.sequence_number)


    def video_send(self):
        print(
            f"sending video to {self.client_address[0]}:{self.client_address[1]}")
        while True:
            if self.server_state == 4:
                return
            if self.server_state != 2:
                sleep(0.5)
                continue
            if (not self.live):
                if self.stream.current_frame_number >= videostream.video_len-1:
                    self.server_state = 3
                    return
            frame = self.stream.get_next_frame()


            # 目前第幾個frame
            frame_number = self.stream.current_frame_number
            rtp_packet = rtp(
                payload_type=rtp.TYPE.MJPEG,
                sequence_number=frame_number,
                timestamp=frame_number*self.period,
                payload=frame
            )
            print(f"Sending packet #{frame_number}")
            packet = rtp_packet.get_packet()
            ##　send rtp packet
            to_send = packet[:]
            while to_send:
                try:
                    self.rtp_socket.sendto(
                        to_send[:4096], self.client_address)
                except socket.error as e:
                    print(f"failed to send rtp packet: {e}")
                to_send = to_send[4096:]
            print(len(packet))
            sleep(self.period/1000.)

    def send_rtsp_response(self, sequence_number):
        response = rtsp.build_response(sequence_number, self.id)
        print(f"Sending to client: {repr(response.encode())}")
        self.rtsp_connection.send(response.encode())
        print('Sent response to client.')
