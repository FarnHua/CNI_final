import cv2

class VideoStream:
    DEFAULT_IMAGE_SHAPE = (380, 280)
    video_len = 500
    fps = 30

    def __init__(self, file_path):
        print(file_path)
        if (file_path != "livestream"):
            self._stream = open(file_path, 'rb')
            self.live = False
        else:
            self._stream = cv2.VideoCapture(0)
            self.live = True
        print('set_up!')
        self.current_frame_number = -1

    def close(self):
        if (self.live):
            self._stream.release()
        else:
            self._stream.close()

    def get_next_frame(self):
        
        if (self.live):
            ret, frame = self._stream.read()
            _, jframe = cv2.imencode('.jpeg', frame)
            print(frame)
            self.current_frame_number += 1
            return bytes(jframe)
        else:
            length = self._stream.read(5)
            print('frame_length', length)
            frame_length = int(length.decode())
            frame = self._stream.read(frame_length)
            self.current_frame_number += 1
            return bytes(frame)


