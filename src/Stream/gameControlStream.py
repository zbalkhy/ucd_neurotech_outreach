from Stream.dataStream import *
import numpy as np
from time import sleep

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
                
                sleep(0.01)  # ~100 Hz control loop
                
        except Exception as e:
            print(f"GameControlStream error: {e}")