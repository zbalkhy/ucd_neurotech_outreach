import numpy as np
import pyqtgraph as pg
from PySide6 import QtCore, QtWidgets

class AudioPlotWidget(QtWidgets.QWidget):
    def __init__(self, audio_source=None, sample_rate=44100):
        super().__init__()
        self.setWindowTitle("Live Plot")
        self.setFixedSize(640, 240)
        self.audio_source = audio_source
        self.sample_rate = sample_rate

        layout = QtWidgets.QVBoxLayout(self)
        self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget)

        self.plot_widget.setBackground('k')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel('left', 'Amplitude')
        self.plot_widget.setYRange(-1, 1)

        self.curve = self.plot_widget.plot(pen=pg.mkPen('c', width=2))

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(30)


    def refresh(self):
        if self.audio_source is None:
            return
        audio = self.audio_source.get_visual_audio(2048)
        self.update_data(audio)

    def update_data(self, audio):
        if audio is None or len(audio) == 0:
            return

        x = np.linspace(0, len(audio) / self.sample_rate, len(audio))
        display_data = audio
        self.curve.setData(x, display_data)


        