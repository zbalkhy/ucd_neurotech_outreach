import sys
import os
import note
import numpy as np
import sounddevice as sd
import soundfile as sf
import threading
from PySide6 import QtCore, QtWidgets
from filters import FilterBank

WHITE_KEY_STYLE = """
QPushButton {
    background-color: qlineargradient(spread:pad, x1:1, y1:0.711, x2:0.903455, y2:0.711, stop:0 rgba(0, 0, 0, 255), stop:1 rgba(255, 255, 255, 255));
}
QPushButton:pressed {
    background-color: rgb(250, 250, 250);
}
"""

BLACK_KEY_STYLE = """
QPushButton {
    background-color: qlineargradient(spread:pad, x1:0.028, y1:0.619, x2:1, y2:0.494, stop:0.852273 rgba(0, 0, 0, 250), stop:1 rgba(255, 255, 255, 255));
}
QPushButton:pressed {
    background-color: qlineargradient(spread:pad, x1:0.857955, y1:0.0170455, x2:1, y2:0, stop:0.125 rgba(0, 0, 0, 255), stop:0.977273 rgba(255, 255, 255, 255));
}
"""

PIANO_KEYS = [
    ('c4', False, 20, 'A'), ('c40', True, 40, 'Q'), ('d4', False, 60, 'S'),
    ('d40', True, 80, 'W'), ('e4', False, 100, 'D'), ('f4', False, 140, 'F'),
    ('f40', True, 160, 'E'), ('g4', False, 180, 'G'), ('g40', True, 200, 'R'),
    ('a4', False, 220, 'H'), ('a40', True, 240, 'T'), ('b4', False, 260, 'J'),
    ('c5', False, 300, 'K'), ('c50', True, 320, 'Y'), ('d5', False, 340, 'L'),
    ('d50', True, 360, 'U'), ('e5', False, 380, 'Z'), ('f5', False, 420, 'X'),
    ('f50', True, 440, 'I'), ('g5', False, 460, 'C'), ('g50', True, 480, 'O'),
    ('a5', False, 500, 'V'), ('a50', True, 520, 'P'), ('b5', False, 540, 'B'),
    ('c6', False, 580, 'N')
]

class Piano(QtWidgets.QWidget):
    def __init__(self, filters: FilterBank | None = None):
        super().__init__()
        self.setWindowTitle("Piano")
        self.setFixedSize(659, 251)
        
        self.sounds = {}
        self.buttons = {}
        self.active_voices = []
        self.filters = filters
        self.visual_buffer_size = 44100
        self.visual_buffer = np.zeros(self.visual_buffer_size, dtype='float32')
        self.visual_write_pos = 0
        self.visual_filled = 0
        self.buffer_lock = threading.Lock()

        self.init_audio()
        self.build_ui()
        

    def init_audio(self):
        """Initialize the output stream once and preload all sounds."""        
        self.stream = sd.OutputStream(
            samplerate=44100,
            channels=2,
            callback=self.audio_callback,
            blocksize=512
        )

        self.stream.start()
        
        for key_data in PIANO_KEYS:
            note_name = key_data[0]
            file_path = f"Sounds/{note_name}.wav"
            
            if os.path.exists(file_path):
                data, samplerate = sf.read(file_path, dtype='float32')
                if samplerate != 44100:
                    print(f"Warning: {file_path} sample rate is {samplerate}, expected 44100.")
                self.sounds[note_name] = data
            else:
                print(f"Warning: {file_path} not found.")

    def build_ui(self):
        # Create buttons
        for name, is_black, x, shortcut in PIANO_KEYS:
            btn = QtWidgets.QPushButton(self)
            btn.setObjectName(name)
            btn.setShortcut(shortcut)
            
            if is_black:
                btn.setGeometry(QtCore.QRect(x, 30, 31, 111))
                btn.setStyleSheet(BLACK_KEY_STYLE)
            else:
                btn.setGeometry(QtCore.QRect(x, 30, 41, 181))
                btn.setStyleSheet(WHITE_KEY_STYLE)
            
            #wire clicks to play the note
            btn.clicked.connect(lambda *args, n=name: self.play_note(n))
            self.buttons[name] = btn

        for name, btn in self.buttons.items():
            is_black = any(k[0] == name and k[1] for k in PIANO_KEYS)
            if is_black:
                btn.raise_()

    def play_note(self, note_name):
        if note_name in self.sounds:
            voice = note.Note(note_name, self.sounds[note_name])
            voice.pointer = 0
            self.active_voices.append(voice)
    
    def audio_callback(self, outdata, frames, time, status):
        outdata.fill(0) #clear the buffer

        for voice in list(self.active_voices):
            start = voice.pointer
            end = start + frames
            chunk = voice.data[start:end]

            if chunk.size == 0:
                self.active_voices.remove(voice)
                continue

            #make 2dim (mono->stereo)
            if chunk.ndim == 1:
                chunk = np.column_stack((chunk, chunk))
            elif chunk.shape[1] == 1:
                chunk = np.repeat(chunk, 2, axis=1)

            outdata[:len(chunk)] += chunk
            voice.pointer = end

            if voice.pointer >= len(voice.data):
                self.active_voices.remove(voice)

        if self.filters is not None:
            outdata[:] = self.filters.apply(outdata)

        with self.buffer_lock:
            mono = np.mean(outdata, axis=1)
            num = len(mono)
            if num > 0:
                end = self.visual_write_pos + num
                if end <= self.visual_buffer_size:
                    self.visual_buffer[self.visual_write_pos:end] = mono
                else:
                    wrap = end - self.visual_buffer_size
                    self.visual_buffer[self.visual_write_pos:] = mono[:num-wrap]
                    self.visual_buffer[:wrap] = mono[num-wrap:]
                self.visual_write_pos = end % self.visual_buffer_size
                self.visual_filled = min(self.visual_buffer_size, self.visual_filled + num)
                
    def get_visual_audio(self, num_samples=2048):
        with self.buffer_lock:
            if self.visual_filled == 0:
                return np.zeros(0, dtype='float32')
            num_samples = min(num_samples, self.visual_filled)
            end = self.visual_write_pos
            start = (end - num_samples) % self.visual_buffer_size
            if start < end:
                return self.visual_buffer[start:end].copy()
            return np.concatenate((self.visual_buffer[start:], self.visual_buffer[:end])).astype('float32')


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Piano(FilterBank(sample_rate=44100))
    window.show()
    sys.exit(app.exec())
    
