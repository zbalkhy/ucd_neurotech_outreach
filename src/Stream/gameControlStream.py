from Stream.dataStream import *
import numpy as np
import scipy.io as sio
from time import sleep
from common import SAMPLING_FREQ

class GameControlStream(DataStream):
    def __init__(self, 
                 reference_stream: DataStream,
                 game: 'InfiniteRunner',
                 active_label: str = 'eyesOpen',  # Which label triggers jump
                 stream_name: str = "GameControl",
                 stream_type: StreamType = StreamType.CONTROL,
                 queue_length: int = QUEUE_LENGTH):
        
        self.reference_stream = reference_stream
        self.game = game
        self.active_label = active_label  # Configurable control mapping
        super().__init__(stream_name, stream_type, queue_length)
    
    def _stream(self):
        try:
            while not self.shutdown_event.is_set():
                # Get the latest data from reference stream
                reference_data = list(self.reference_stream.get_stream_data())
                
                if len(reference_data) > 0:
                    # Take the most recent classifier output (string label)
                    current_label = reference_data[-1]
                    
                    # Handle both string and array formats
                    if isinstance(current_label, np.ndarray):
                        current_label = current_label[0]
                    
                    # Map label to game control
                    if current_label == self.active_label:
                        self.game.space_pressed = True   # Move to top lane
                    else:
                        self.game.space_pressed = False  # Move to bottom lane
                    
                    # Store for monitoring
                    self.data.append(current_label)
                    
                    print(f"Brain State: {current_label} | Top Lane: {self.game.space_pressed}")
                
                sleep(1/60) # pygame runs at 60fps
                
        except Exception as e:
            print(f"GameControlStream error: {e}")

# ADDED MATFILE STREAM TO GRAB DATA FROM DATA.MAT

class MatFileStream(DataStream):
    def __init__(self, mat_path, stream_name="EEG_Mat", stream_type=StreamType.SOFTWARE, queue_length=QUEUE_LENGTH):
        mat = sio.loadmat(mat_path)
        eyes_open = mat['eyesOpen']     # shape (10, 250)
        eyes_closed = mat['eyesClosed'] # shape (10, 250)
        self.samples = []
        for i in range(eyes_open.shape[0]):
            self.samples.extend(eyes_open[i])
            self.samples.extend(eyes_closed[i])
        self.sample_index = 0
        super().__init__(stream_name, stream_type, queue_length)

    def _stream(self):
        while not self.shutdown_event.is_set():
            if self.sample_index < len(self.samples):
                self.data.append(np.array([self.samples[self.sample_index]]))
                self.sample_index += 1
            else:
                self.sample_index = 0
            sleep(1/SAMPLING_FREQ)