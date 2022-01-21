from PyQt5.QtWidgets import QApplication
import sys
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import pyqtSignal, QTimer, Qt
from PIL.ImageQt import ImageQt

from client_func import client_func
from video_stream import videostream
import time


class ClientWindow(QMainWindow):
    image_thread = pyqtSignal()

    def __init__(self,file_name: str,host_address: str,host_port: int,rtp_port: int,parent=None):
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

        self.host_address = host_address
        self.host_port = host_port
        self.rtp_port = rtp_port

        self.client = client_func(file_name, host_address, host_port, rtp_port)
        self.image_thread.connect(self.renew_image)
        self.timer = QTimer()
        self.timer.timeout.connect(self.image_thread.emit)

        self.create_ui()

    def create_ui(self):
        self.setWindowTitle("Client")
        self.setStyleSheet("background-color: rgb(255, 244, 212)")

        self.setup_button.setEnabled(True)
        self.setup_button.setText('Setup')
        self.setup_button.clicked.connect(self.setup)

        self.play_button.setEnabled(False)
        self.play_button.setText('Play')
        self.play_button.clicked.connect(self.play)

        self.pause_button.setEnabled(False)
        self.pause_button.setText('Pause')
        self.pause_button.clicked.connect(self.pause)

        self.tear_button.setEnabled(False)
        self.tear_button.setText('Teardown')
        self.tear_button.clicked.connect(self.teardown)

        self.video1_button.setEnabled(False)
        self.video1_button.setText('Video1')
        self.video1_button.clicked.connect(self.select1)

        self.video2_button.setEnabled(False)
        self.video2_button.setText('Video2')
        self.video2_button.clicked.connect(self.select2)

        self.video3_button.setEnabled(False)
        self.video3_button.setText('Video3')
        self.video3_button.clicked.connect(self.select3)

        self.livestream_button.setEnabled(False)
        self.livestream_button.setText('LiveStream')
        self.livestream_button.clicked.connect(self.select_live)       

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

        central_widget.setLayout(layout)

    def renew_image(self):
        if not self.client.rtp_receiving_status:
            return
        frame = None
        if self.client.video_buffer:
            self.client.frame_number += 1
            frame = self.client.video_buffer.pop(0), self.client.frame_number
        if frame is not None:
            pix = QPixmap.fromImage(ImageQt(frame[0]).copy())
            self.video_player.setPixmap(pix)

    def setup(self):
        self.client.establish_rtsp_connection()
        self.client.send_setup_request()
        self.setup_button.setEnabled(False)
        self.play_button.setEnabled(True)
        self.tear_button.setEnabled(True)
        self.video1_button.setEnabled(True)
        self.video2_button.setEnabled(True)
        self.video3_button.setEnabled(True)
        self.livestream_button.setEnabled(True)
        self.timer.start(1000//videostream.fps)

    def play(self):
        self.client.send_play_request()
        self.play_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.video1_button.setEnabled(False)
        self.video2_button.setEnabled(False)
        self.video3_button.setEnabled(False)
        self.livestream_button.setEnabled(False)

    def pause(self):
        self.client.send_pause_request()
        self.pause_button.setEnabled(False)
        self.play_button.setEnabled(True)
        self.video1_button.setEnabled(True)
        self.video2_button.setEnabled(True)
        self.video3_button.setEnabled(True)
        self.livestream_button.setEnabled(True)     

    def teardown(self):
        self.client.send_teardown_request()
        self.setup_button.setEnabled(True)
        self.play_button.setEnabled(False)
        self.pause_button.setEnabled(False)
        self.video1_button.setEnabled(False)
        self.video2_button.setEnabled(False)
        self.video3_button.setEnabled(False)
        self.livestream_button.setEnabled(False)
        exit(0)
    
    def select1(self):
        #First, Teardown
        self.client.send_teardown_request()
        self.client.rtp_socket.close()
        time.sleep(5)
        #Then, new setup
        print(self.host_address, self.host_port, self.rtp_port)
        self.client = client_func("chloe.mjpg", self.host_address, self.host_port, self.rtp_port)
        self.client.establish_rtsp_connection()
        self.client.send_setup_request()
        self.timer.start(1000//videostream.fps)

        #UI Change
        self.play_button.setEnabled(True)
        self.pause_button.setEnabled(True)
        self.video1_button.setEnabled(False)
        self.video2_button.setEnabled(False)
        self.video3_button.setEnabled(False)
        self.livestream_button.setEnabled(False)
    
    def select2(self):
        #First, Teardown
        self.client.send_teardown_request()
        self.client.rtp_socket.close()
        time.sleep(5)
        #Then, new setup
        print(self.host_address, self.host_port, self.rtp_port)
        self.client = client_func("jf2.mjpg", self.host_address, self.host_port, self.rtp_port)
        self.client.establish_rtsp_connection()
        self.client.send_setup_request()
        self.timer.start(1000//videostream.fps)
  
        #UI Change
        self.play_button.setEnabled(True)
        self.pause_button.setEnabled(True)
        self.video1_button.setEnabled(False)
        self.video2_button.setEnabled(False)
        self.video3_button.setEnabled(False)
        self.livestream_button.setEnabled(False)
    
    def select3(self):
        #First, Teardown
        self.client.send_teardown_request()
        self.client.rtp_socket.close()
        time.sleep(5)
        #Then, new setup
        print(self.host_address, self.host_port, self.rtp_port)
        self.client = client_func("4.mjpg", self.host_address, self.host_port, self.rtp_port)
        self.client.establish_rtsp_connection()
        self.client.send_setup_request()
        self.timer.start(1000//videostream.fps)
        
        #UI Change
        self.play_button.setEnabled(True)
        self.pause_button.setEnabled(True)
        self.video1_button.setEnabled(False)
        self.video2_button.setEnabled(False)
        self.video3_button.setEnabled(False)
        self.livestream_button.setEnabled(False)
    
    def select_live(self):
        #First, Teardown
        self.client.send_teardown_request()
        self.client.rtp_socket.close()
        time.sleep(5)
        #Then, new setup
        print(self.host_address, self.host_port, self.rtp_port)
        self.client = client_func("livestream", self.host_address, self.host_port, self.rtp_port)
        self.client.establish_rtsp_connection()
        self.client.send_setup_request()
        self.timer.start(1000//videostream.fps)

        #UI Change
        self.play_button.setEnabled(True)
        self.pause_button.setEnabled(True)
        self.video1_button.setEnabled(False)
        self.video2_button.setEnabled(False)
        self.video3_button.setEnabled(False)
        self.livestream_button.setEnabled(False)
    




if __name__ == '__main__':

    if len(sys.argv) != 4:
        print(f"Please type in: {sys.argv[0].split('/')[-1]} <host address> <host port> <RTP port>")
        exit(-1)
    
    host_address, host_port, rtp_port = *sys.argv[1:],

    try:
        host_port = int(host_port)
        rtp_port = int(rtp_port)
    except ValueError:
        raise ValueError('port values should be integer')

    app = QApplication(sys.argv)
    client = ClientWindow("livestream", host_address, host_port, rtp_port)
    client.resize(400, 300)
    client.show()
    sys.exit(app.exec_())
