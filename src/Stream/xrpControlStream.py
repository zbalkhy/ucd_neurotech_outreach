from Stream.dataStream import *
import serial

class XRPControlStream(DataStream):
    def __init__(self, reference_stream: DataStream, 
               port: str, baudrate: int, timeout:int,
               stream_name: str,
               stream_type: StreamType,
               queue_length: int = QUEUE_LENGTH):
        self.reference_stream: DataStream = reference_stream
        self.port: str = port
        self.baudrate: int = baudrate
        self.timeout: int = timeout
        super().__init__(stream_name, stream_type, queue_length)
        
    def _stream(self):
        try:
            self.ser = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)
            while not self.shutdown_event.is_set():
                 reference_stream_data = list(self.reference_stream.get_stream_data())
                 if len(reference_stream_data) > 0:
                    # take the last element in the stream data as the command
                    command = reference_stream_data[-1]
                    ser_output = str(command) + "\n"
                    print(ser_output)
                    self.ser.write(ser_output.encode())

        except Exception as e:
            print(e)