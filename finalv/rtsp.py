import re

class InvalidRTSPRequest(Exception):
    pass

class rtsp:
    RTSP_VERSION = 'RTSP/1.0'

    INVALID = -1
    SETUP = 'SETUP'
    PLAY = 'PLAY'
    PAUSE = 'PAUSE'
    TEARDOWN = 'TEARDOWN'
    RESPONSE = 'RESPONSE'

    def __init__(self,request_type,video_file_path = None,sequence_number = None,destination_port = None,id = None):
        self.request_type = request_type
        self.file_path = video_file_path
        self.sequence_number = sequence_number
        self.id = id
        self.rtp_destination_port = destination_port

    def __str__(self):
        return (f"RTSPPacket({self.request_type}, "f"{self.file_path}, "f"{self.sequence_number}, "f"{self.rtp_destination_port}, "f"{self.id})")
    @classmethod

    def receive(cls, request):
        match = re.match(
            r"(?P<request_type>\w+) rtsp://(?P<video_file_path>\S+) (?P<rtsp_version>RTSP/\d+.\d+)\r?\n"
            r"CSeq: (?P<sequence_number>\d+)\r?\n"
            r"(Range: (?P<play_range>\w+=\d+-\d+\r?\n))?"
            r"(Transport: .*client_port=(?P<dst_port>\d+).*\r?\n)?"  # in case of SETUP request
            r"(Session: (?P<id>\d+)\r?\n)?",
            request.decode()
        )

        if match is None:
            raise InvalidRTSPRequest(f"failed to parse request: {request}")

        g = match.groupdict()
        request_type = g.get('request_type')

        if request_type not in (rtsp.SETUP,rtsp.PLAY,rtsp.PAUSE,rtsp.TEARDOWN):
            raise InvalidRTSPRequest(f"invalid request type: {request}")

        file_path = g.get('video_file_path')
        sequence_number = g.get('sequence_number')
        destination_port = g.get('dst_port')
        id = g.get('id')

        if request_type == rtsp.SETUP:
            try:
                destination_port = int(destination_port)
            except (ValueError, TypeError):
                raise InvalidRTSPRequest(f"failed to parse RTP port")
        try:
            sequence_number = int(sequence_number)
        except (ValueError, TypeError):
            raise InvalidRTSPRequest(f"failed to parse sequence number: {request}")

        return cls(request_type,file_path,sequence_number,destination_port,id)

    def response(self):
        if any((attr is None for attr in (self.request_type,self.sequence_number,self.id))):
            raise InvalidRTSPRequest('missing one attribute of: `request_type`, `sequence_number`, `id`')

        if self.request_type in (self.INVALID, self.RESPONSE):
            raise InvalidRTSPRequest(f"invalid request type: {self}")

        request_lines = [
            f"{self.request_type} rtsp://{self.file_path} {self.RTSP_VERSION}",
            f"CSeq: {self.sequence_number}",
        ]
        if self.request_type == self.SETUP:
            if self.rtp_destination_port is None:
                raise InvalidRTSPRequest(f"missing RTP destination port: {self}")
            request_lines.append(
                f"Transport: RTP/UDP;client_port={self.rtp_destination_port}"
            )
        else:
            request_lines.append(
                f"Session: {self.id}"
            )
        request = '\r\n'.join(request_lines) + '\r\n'
        return request.encode()
        
    @classmethod
    def from_response(cls, response):
        match = re.match(r"(?P<rtsp_version>RTSP/\d+.\d+) 200 OK\r?\n"r"CSeq: (?P<sequence_number>\d+)\r?\n"r"Session: (?P<id>\d+)\r?\n",response.decode())

        if match is None:
            raise Exception(f"failed to parse RTSP response: {response}")

        g = match.groupdict()

        sequence_num = g.get('sequence_number')
        id = g.get('id')

        try:
            sequence_num = int(sequence_num)
        except (ValueError, TypeError):
            raise Exception(f"failed to parse sequence number: {response}")

        if id is None:
            raise Exception(f"failed to parse session id: {response}")

        return cls(request_type=rtsp.RESPONSE,sequence_number=sequence_num,id=id)

    @classmethod
    def build_response(cls, sequence_number, id):
        response = '\r\n'.join((f"{cls.RTSP_VERSION} 200 OK",f"CSeq: {sequence_number}",f"Session: {id}",)) + '\r\n'
        return response

