import cv2

class VideoStream:
    FRAME_HEADER_LENGTH = 5
    DEFAULT_IMAGE_SHAPE = (380, 280)
    VIDEO_LENGTH = 500
    # DEFAULT_FPS = 24
    DEFAULT_FPS = 30
    # if it's present at the end of chunk,
    # it's the last chunk for current jpeg (end of frame)
    JPEG_EOF = b'\xff\xd9'

    def __init__(self, file_path: str or None = None):
        # for simplicity, mjpeg is assumed to be on working directory
        if (file_path):
            self._stream = open(file_path, 'rb')
            self.live = False
        else:
            self._stream = cv2.VideoCapture(0)
            self.live = True
        print('set_up!')
        # frame number is zero-indexed
        # after first frame is sent, this is set to zero
        self.current_frame_number = -1

    def close(self):
        if (self.live):
            self._stream.release()
        else:
            self._stream.close()

    def get_next_frame(self) -> bytes:
        # sample video file format is as follows:
        # - 5 digit integer `frame_length` written as 5 bytes, one for each digit (ascii)
        # - `frame_length` bytes follow, which represent the frame encoded as a JPEG
        # - repeat until EOF
        
        if (self.live):
            ret, frame = self._stream.read()
            _, jframe = cv2.imencode('.jpeg', frame)
            print(frame)
            self.current_frame_number += 1
            return bytes(jframe)
        else:
            try:
                frame_length = self._stream.read(self.FRAME_HEADER_LENGTH)
                print('frame_length', frame_length)
            except ValueError:
                raise EOFError
            frame_length = int(frame_length.decode())
            frame = self._stream.read(frame_length)
            self.current_frame_number += 1
            return bytes(frame)


