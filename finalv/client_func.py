import socket
from threading import Thread
from time import sleep
from PIL import Image
from io import BytesIO
from rtsp import rtsp
from rtp import rtp


class client_func:

    def __init__( self, file_path, remote_host_address, remote_host_port, rtp_port):
        self.rtsp_connection = None
        self.rtp_socket = None
        self.rtp_receive_thread = None
        self.buffer = []
        self.sequence_number = 0
        self.id = ''
        self.current_frame_number = -1
        self.is_rtsp_connected = False
        self.is_receiving_rtp = False
        self.file_path = file_path
        self.remote_host_address = remote_host_address
        self.remote_host_port = remote_host_port
        self.rtp_port = rtp_port

    # def get_next_frame(self):
    #     if self.buffer:
    #         self.current_frame_number += 1
    #         return self.buffer.pop(0), self.current_frame_number
    #     return None


    def video_receive(self):
        self.rtp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rtp_socket.bind(('localhost', self.rtp_port))
        self.rtp_socket.settimeout(5 / 1000.)
        while True:
            if not self.is_receiving_rtp:
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
            self.buffer.append(frame)

    def establish_rtsp_connection(self):
        if self.is_rtsp_connected:
            return
        self.rtsp_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rtsp_connection.connect((self.remote_host_address, self.remote_host_port))
        self.rtsp_connection.settimeout(0.1)
        self.is_rtsp_connected = True

    def close_rtsp_connection(self):
        if not self.is_rtsp_connected:
            return
        self.rtsp_connection.close()
        self.is_rtsp_connected = False

    def send_request(self, type = rtsp.INVALID):
        if not self.is_rtsp_connected:
            raise Exception('rtsp connection not established. run `setup_rtsp_connection()`')
        request = rtsp(type,self.file_path, self.sequence_number, self.rtp_port,self.id).to_request()
        self.rtsp_connection.send(request)
        self.sequence_number += 1
        rcv = None
        while True:
            try:
                rcv = self.rtsp_connection.recv(4096)
                break
            except socket.timeout:
                continue
        response = rtsp.from_response(rcv)
        return response

    def send_setup_request(self):
        response = self.send_request(rtsp.SETUP)
        self.rtp_receive_thread = Thread(target=self.video_receive, daemon=True)
        self.rtp_receive_thread.start()
        self.id = response.id
        return response

    def send_play_request(self):
        response = self.send_request(rtsp.PLAY)
        self.is_receiving_rtp = True
        return response

    def send_pause_request(self):
        response = self.send_request(rtsp.PAUSE)
        self.is_receiving_rtp = False
        return response

    def send_teardown_request(self):
        response = self.send_request(rtsp.TEARDOWN)
        self.is_receiving_rtp = False
        self.is_rtsp_connected = False
        return response
