from turtle import rt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import pyqtSignal, QTimer, Qt
from PIL.ImageQt import ImageQt

from client.client import Client
from utils.video_stream import VideoStream
import time


class ClientWindow(QMainWindow):
    _update_image_signal = pyqtSignal()

    def __init__(
            self,
            file_name: str,
            host_address: str,
            host_port: int,
            rtp_port: int,
            parent=None):
        super(ClientWindow, self).__init__(parent)
        self.video_player = QLabel()

        self.setup_button = QPushButton()
        self.play_button = QPushButton()
        self.pause_button = QPushButton()
        self.tear_button = QPushButton()
        self.video1_button = QPushButton()
        self.video2_button = QPushButton()
        self.video3_button = QPushButton()
        self.livestream_button = QPushButton()
        
        
        self.select = QLabel()
        self.control = QLabel()

        self.error_label = QLabel()
        self.host_address = host_address
        self.host_port = host_port
        self.rtp_port = rtp_port

        self._media_client = Client(file_name, host_address, host_port, rtp_port)
        self._update_image_signal.connect(self.update_image)
        self._update_image_timer = QTimer()
        self._update_image_timer.timeout.connect(
            self._update_image_signal.emit)

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Client")
        self.setStyleSheet("background-color: rgb(255, 244, 212)")

        self.setup_button.setEnabled(True)
        self.setup_button.setText('Setup')
        self.setup_button.clicked.connect(self.handle_setup)

        self.play_button.setEnabled(False)
        self.play_button.setText('Play')
        self.play_button.clicked.connect(self.handle_play)

        self.pause_button.setEnabled(False)
        self.pause_button.setText('Pause')
        self.pause_button.clicked.connect(self.handle_pause)

        self.tear_button.setEnabled(False)
        self.tear_button.setText('Teardown')
        self.tear_button.clicked.connect(self.handle_teardown)

        self.video1_button.setEnabled(False)
        self.video1_button.setText('Video1')
        self.video1_button.clicked.connect(self.handle_select1)

        self.video2_button.setEnabled(False)
        self.video2_button.setText('Video2')
        self.video2_button.clicked.connect(self.handle_select2)

        self.video3_button.setEnabled(False)
        self.video3_button.setText('Video3')
        self.video3_button.clicked.connect(self.handle_select3)

        self.livestream_button.setEnabled(False)
        self.livestream_button.setText('LiveStream')
        self.livestream_button.clicked.connect(self.handle_select_live)       


        self.error_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        font =QFont()
        font.setPointSize(15)
        font.setBold(True)
        font.setWeight(75)
        self.control.setFont(font)     
        self.control.setAlignment(Qt.AlignCenter)
        self.control.setText("Control")
        self.select.setFont(font)     
        self.select.setAlignment(Qt.AlignCenter)
        self.select.setText("Select")

        control_layout = QVBoxLayout()
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.addWidget(self.control)
        control_layout.addWidget(self.setup_button)
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.pause_button)
        control_layout.addWidget(self.tear_button)

        select_layout = QVBoxLayout()
        select_layout.addWidget(self.select)
        select_layout.addWidget(self.video1_button)
        select_layout.addWidget(self.video2_button)
        select_layout.addWidget(self.video3_button)
        select_layout.addWidget(self.livestream_button)

        userInput_layout = QVBoxLayout()
        userInput_layout.addLayout(control_layout)
        userInput_layout.addLayout(select_layout)

        layout = QHBoxLayout()
        layout.addWidget(self.video_player)
        layout.addLayout(userInput_layout)
        layout.addWidget(self.error_label)

        central_widget.setLayout(layout)

    def update_image(self):
        if not self._media_client.is_receiving_rtp:
            return
        frame = self._media_client.get_next_frame()
        if frame is not None:
            pix = QPixmap.fromImage(ImageQt(frame[0]).copy())
            self.video_player.setPixmap(pix)

    def handle_setup(self):
        self._media_client.establish_rtsp_connection()
        self._media_client.send_setup_request()
        self.setup_button.setEnabled(False)
        self.play_button.setEnabled(True)
        self.tear_button.setEnabled(True)
        self.video1_button.setEnabled(True)
        self.video2_button.setEnabled(True)
        self.video3_button.setEnabled(True)
        self.livestream_button.setEnabled(True)
        self._update_image_timer.start(1000//VideoStream.fps)

    def handle_play(self):
        self._media_client.send_play_request()
        self.play_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.video1_button.setEnabled(False)
        self.video2_button.setEnabled(False)
        self.video3_button.setEnabled(False)
        self.livestream_button.setEnabled(False)

    def handle_pause(self):
        self._media_client.send_pause_request()
        self.pause_button.setEnabled(False)
        self.play_button.setEnabled(True)
        self.video1_button.setEnabled(True)
        self.video2_button.setEnabled(True)
        self.video3_button.setEnabled(True)
        self.livestream_button.setEnabled(True)     

    def handle_teardown(self):
        self._media_client.send_teardown_request()
        self.setup_button.setEnabled(True)
        self.play_button.setEnabled(False)
        self.pause_button.setEnabled(False)
        self.video1_button.setEnabled(False)
        self.video2_button.setEnabled(False)
        self.video3_button.setEnabled(False)
        self.livestream_button.setEnabled(False)
        exit(0)
    
    def handle_select1(self):
        #First, Teardown
        self._media_client.send_teardown_request()
        self._media_client._rtp_socket.close()
        time.sleep(5)
        #Then, new setup
        print(self.host_address, self.host_port, self.rtp_port)
        self._media_client = Client("chloe.mjpg", self.host_address, self.host_port, self.rtp_port)
        self._media_client.establish_rtsp_connection()
        self._media_client.send_setup_request()
        self._update_image_timer.start(1000//VideoStream.fps)
        #New client? 
        
        #UI Change
        self.play_button.setEnabled(True)
        self.pause_button.setEnabled(True)
        self.video1_button.setEnabled(False)
        self.video2_button.setEnabled(False)
        self.video3_button.setEnabled(False)
        self.livestream_button.setEnabled(False)
    
    def handle_select2(self):
        # print("here")
        #First, Teardown
        self._media_client.send_teardown_request()
        self._media_client._rtp_socket.close()
        time.sleep(5)
        #Then, new setup
        print(self.host_address, self.host_port, self.rtp_port)
        self._media_client = Client("jf2.mjpg", self.host_address, self.host_port, self.rtp_port)
        self._media_client.establish_rtsp_connection()
        self._media_client.send_setup_request()
        self._update_image_timer.start(1000//VideoStream.fps)
        #New client? 
        
        #UI Change
        self.play_button.setEnabled(True)
        self.pause_button.setEnabled(True)
        self.video1_button.setEnabled(False)
        self.video2_button.setEnabled(False)
        self.video3_button.setEnabled(False)
        self.livestream_button.setEnabled(False)
    
    def handle_select3(self):
        # print("here")
        #First, Teardown
        self._media_client.send_teardown_request()
        self._media_client._rtp_socket.close()
        time.sleep(5)
        #Then, new setup
        print(self.host_address, self.host_port, self.rtp_port)
        self._media_client = Client("4.mjpg", self.host_address, self.host_port, self.rtp_port)
        self._media_client.establish_rtsp_connection()
        self._media_client.send_setup_request()
        self._update_image_timer.start(1000//VideoStream.fps)
        #New client? 
        
        #UI Change
        self.play_button.setEnabled(True)
        self.pause_button.setEnabled(True)
        self.video1_button.setEnabled(False)
        self.video2_button.setEnabled(False)
        self.video3_button.setEnabled(False)
        self.livestream_button.setEnabled(False)
    
    def handle_select_live(self):
        # print("here")
        #First, Teardown
        self._media_client.send_teardown_request()
        self._media_client._rtp_socket.close()
        time.sleep(5)
        #Then, new setup
        print(self.host_address, self.host_port, self.rtp_port)
        self._media_client = Client("livestream", self.host_address, self.host_port, self.rtp_port)
        self._media_client.establish_rtsp_connection()
        self._media_client.send_setup_request()
        self._update_image_timer.start(1000//VideoStream.fps)
        #New client? 
        
        #UI Change
        self.play_button.setEnabled(True)
        self.pause_button.setEnabled(True)
        self.video1_button.setEnabled(False)
        self.video2_button.setEnabled(False)
        self.video3_button.setEnabled(False)
        self.livestream_button.setEnabled(False)
    
    


    def handle_error(self):
        self.play_button.setEnabled(False)
        self.pause_button.setEnabled(False)
        self.tear_button.setEnabled(False)
        self.error_label.setText(f"Error: {self.media_player.errorString()}")
