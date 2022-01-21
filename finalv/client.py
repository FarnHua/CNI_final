from PyQt5.QtWidgets import QApplication
import sys
from UI import ClientWindow


if __name__ == '__main__':

    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0].split('/')[-1]} <host address> <host port> <RTP port>")
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
