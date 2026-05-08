from PySide6 import QtWidgets
from piano import Piano
from filters import FilterBank
from visualizer import AudioPlotWidget


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    print("main app starting")
    filters = FilterBank(sample_rate=44100)

    main_window = QtWidgets.QMainWindow()
    main_window.setWindowTitle("Piano App")
    central_widget = QtWidgets.QWidget()
    main_window.setCentralWidget(central_widget)

    main_layout = QtWidgets.QHBoxLayout(central_widget)

    left_panel = QtWidgets.QWidget()
    left_layout = QtWidgets.QVBoxLayout(left_panel)
    piano_widget = Piano(filters)
    graph = AudioPlotWidget(audio_source=piano_widget, sample_rate=44100)
    left_layout.addWidget(piano_widget)
    left_layout.addWidget(graph)

    right_panel = QtWidgets.QWidget()
    right_panel.setFixedWidth(260)
    right_panel.setStyleSheet("background-color: #222; border: 1px solid #444;")
    right_layout = QtWidgets.QVBoxLayout(right_panel)

    right_layout.addWidget(filters)

    main_layout.addWidget(left_panel, 1)
    main_layout.addWidget(right_panel)

    main_window.show()
    app.exec()

