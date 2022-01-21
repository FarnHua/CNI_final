import socket
from threading import Thread
from time import sleep
from PIL import Image
from io import BytesIO
from utils.rtsp_packet import rtsp
from utils.rtp_packet import RTPPacket


class Client:

    def __init__( self, file_path, remote_host_address, remote_host_port, rtp_port):
        self._rtsp_connection = None
        self._rtp_socket = None
        self._rtp_receive_thread = None
        self._frame_buffer = []
        self._current_sequence_number = 0
        self.id = ''
        self.current_frame_number = -1
        self.is_rtsp_connected = False
        self.is_receiving_rtp = False
        self.file_path = file_path
        self.remote_host_address = remote_host_address
        self.remote_host_port = remote_host_port
        self.rtp_port = rtp_port

    def get_next_frame(self):
        if self._frame_buffer:
            self.current_frame_number += 1
            return self._frame_buffer.pop(0), self.current_frame_number
        return None


    def video_receive(self):
        self._rtp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._rtp_socket.bind((self.remote_host_address, self.rtp_port))
        self._rtp_socket.settimeout(5 / 1000.)
        while True:
            if not self.is_receiving_rtp:
                sleep(5/1000.)  
                continue
            recv = bytes()
            while True:
                try:
                    recv += self._rtp_socket.recv(4096)
                    if recv.endswith(b'\xff\xd9'):
                        break
                except socket.timeout:
                    continue
            packet = RTPPacket.from_packet(recv)
            frame = Image.open(BytesIO(packet.payload))
            self._frame_buffer.append(frame)

    def establish_rtsp_connection(self):
        if self.is_rtsp_connected:
            return
        self._rtsp_connection = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        self._rtsp_connection.connect(
            (self.remote_host_address, self.remote_host_port))
        self._rtsp_connection.settimeout(0.1)
        self.is_rtsp_connected = True

    def close_rtsp_connection(self):
        if not self.is_rtsp_connected:
            return
        self._rtsp_connection.close()
        self.is_rtsp_connected = False

    def send_request(self, request_type = rtsp.INVALID):
        if not self.is_rtsp_connected:
            raise Exception('rtsp connection not established. run `setup_rtsp_connection()`')
        request = rtsp(request_type,self.file_path, self._current_sequence_number, self.rtp_port,self.id).to_request()
        self._rtsp_connection.send(request)
        self._current_sequence_number += 1
        rcv = None
        while True:
            try:
                rcv = self._rtsp_connection.recv(4096)
                break
            except socket.timeout:
                continue
        print(f"Received from server: {repr(rcv)}")
        response = rtsp.from_response(rcv)
        return response

    def send_setup_request(self):
        response = self.send_request(rtsp.SETUP)
        self._rtp_receive_thread = Thread(target=self.video_receive, daemon=True)
        self._rtp_receive_thread.start()
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
