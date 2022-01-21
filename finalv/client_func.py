import socket
from threading import Thread
from time import sleep
from PIL import Image
from io import BytesIO
from rtsp import rtsp
from rtp import rtp


class client_func:

    def __init__( self, file_path, host, host_port, rtp_port):
        self.rtsp_connect = None
        self.rtp_socket = None
        self.rtp_thread = None
        self.video_buffer = []
        self.sequence_number = 0
        self.id = ''
        self.frame_number = -1
        self.rtsp_connection_status = False
        self.rtp_receiving_status = False
        self.file_path = file_path
        self.host_address = host
        self.host_port = host_port
        self.rtp_port = rtp_port

    def establish_rtsp_connection(self):
        if self.rtsp_connection_status:
            return
        self.rtsp_connect = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rtsp_connect.connect((self.host_address, self.host_port))
        self.rtsp_connect.settimeout(0.1)
        self.rtsp_connection_status = True

    def send_request(self, type = rtsp.INVALID):
        if not self.rtsp_connection_status:
            raise Exception('rtsp connection not established. run `setup_rtsp_connection()`')
        request = rtsp(type,self.file_path, self.sequence_number, self.rtp_port,self.id).response()
        self.rtsp_connect.send(request)
        self.sequence_number += 1
        rcv = None
        while True:
            try:
                rcv = self.rtsp_connect.recv(4096)
                break
            except socket.timeout:
                continue
        response = rtsp.from_response(rcv)
        return response

    def send_setup_request(self):
        response = self.send_request(rtsp.SETUP)
        self.rtp_thread = Thread(target=self.video_receive, daemon=True)
        self.rtp_thread.start()
        self.id = response.id
        return response

    def send_play_request(self):
        self.rtp_receiving_status = True        
        response = self.send_request(rtsp.PLAY)
        return response

    def video_receive(self):
        self.rtp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rtp_socket.bind(('localhost', self.rtp_port))
        self.rtp_socket.settimeout(5 / 1000.)
        while True:
            if not self.rtp_receiving_status:
                sleep(5/1000.)  
                continue
            recv = bytes()
            while True:
                try:
                    recv += self.rtp_socket.recv(4096)
                    if recv.endswith(b'\xff\xd9'):
                        break
                except socket.timeout:
                    continue
            packet = rtp.from_packet(recv)
            frame = Image.open(BytesIO(packet.payload))
            self.video_buffer.append(frame)

    def send_pause_request(self):
        self.rtp_receiving_status = False
        response = self.send_request(rtsp.PAUSE)
        return response

    def send_teardown_request(self):
        self.rtp_receiving_status = False
        self.rtsp_connection_status = False
        response = self.send_request(rtsp.TEARDOWN)
        return response

    def close_rtsp_connection(self):
            if not self.rtsp_connection_status:
                return
            self.rtsp_connect.close()
            self.rtsp_connection_status = False