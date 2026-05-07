from scipy import signal
from PyQt6 import QtCore, QtWidgets

FILTER_TYPES = ["lowpass", "highpass", "bandpass", "bandstop"]


class FilterBank(QtWidgets.QWidget):
    def __init__(self, sample_rate, parent=None):
        super().__init__(parent)
        self.sample_rate = sample_rate
        self.filters = {}
        self.setStyleSheet("color: white;")
        self.build_ui()

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        header = QtWidgets.QLabel("Filters")
        header.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")
        layout.addWidget(header)
        layout.addSpacing(10)

        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText("filter name")

        self.type_select = QtWidgets.QComboBox()
        self.type_select.addItems(FILTER_TYPES)

        self.cutoff_input = QtWidgets.QLineEdit()
        self.cutoff_input.setPlaceholderText("1000 or 500,2000")

        self.order_input = QtWidgets.QSpinBox()
        self.order_input.setRange(1, 12)
        self.order_input.setValue(4)

        self.add_button = QtWidgets.QPushButton("Add Filter")
        self.remove_button = QtWidgets.QPushButton("Remove Filter")
        self.filter_list = QtWidgets.QListWidget()
        self.filter_list.setStyleSheet("background-color: #111; color: white;")
        self.filter_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.filter_list.setFixedHeight(180)

        self.status_label = QtWidgets.QLabel("")
        self.status_label.setStyleSheet("color: #aaffaa;")

        layout.addWidget(QtWidgets.QLabel("Name:"))
        layout.addWidget(self.name_input)
        layout.addWidget(QtWidgets.QLabel("Type:"))
        layout.addWidget(self.type_select)
        layout.addWidget(QtWidgets.QLabel("Cutoff (Hz):"))
        layout.addWidget(self.cutoff_input)
        layout.addWidget(QtWidgets.QLabel("Order:"))
        layout.addWidget(self.order_input)
        layout.addWidget(self.add_button)
        layout.addWidget(self.remove_button)
        layout.addSpacing(10)
        layout.addWidget(self.filter_list)
        layout.addWidget(self.status_label)
        layout.addStretch(1)

        self.add_button.clicked.connect(self.add_filter)
        self.remove_button.clicked.connect(self.remove_filter)
        self.filter_list.itemSelectionChanged.connect(self.on_filter_selected)

        self.update_filter_list()

    def show_status(self, message, error=False):
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: #ff6666;" if error else "color: #aaffaa;")

    def parse_cutoff_text(self, text, filter_type):
        if not text:
            raise ValueError("Cutoff frequency is required.")

        parts = [p.strip() for p in text.split(",") if p.strip()]
        values = [float(p) for p in parts]

        if filter_type in ("bandpass", "bandstop"):
            if len(values) != 2:
                raise ValueError("Bandpass and bandstop require two cutoff values separated by a comma.")
            if values[0] >= values[1]:
                raise ValueError("The first cutoff value must be less than the second.")
            return values

        if len(values) != 1:
            raise ValueError("Lowpass and highpass require a single cutoff frequency.")

        return values[0]

    def update_filter_list(self):
        self.filter_list.clear()
        for name, (sos, filter_type, cutoff, order) in self.filters.items():
            cutoff_text = ",".join(str(c) for c in cutoff) if isinstance(cutoff, (list, tuple)) else str(cutoff)
            item = QtWidgets.QListWidgetItem(f"{name} ({filter_type}, {cutoff_text} Hz, order {order})")
            item.setData(QtCore.Qt.ItemDataRole.UserRole, name)
            self.filter_list.addItem(item)

    def add_filter(self):
        name = self.name_input.text().strip()
        if not name:
            self.show_status("Enter a filter name.", True)
            return

        filter_type = self.type_select.currentText()
        cutoff_text = self.cutoff_input.text().strip()
        try:
            cutoff_value = self.parse_cutoff_text(cutoff_text, filter_type)
            order_value = self.order_input.value()
            self.add(name, filter_type, cutoff_value, order_value)
            self.update_filter_list()
            self.show_status(f"Added filter '{name}'.")
        except Exception as exc:
            self.show_status(str(exc), True)

    def remove_filter(self):
        selected_item = self.filter_list.currentItem()
        name = selected_item.data(QtCore.Qt.ItemDataRole.UserRole) if selected_item else self.name_input.text().strip()
        if not name:
            self.show_status("Select or enter a filter name to remove.", True)
            return

        if name not in self.filters:
            self.show_status(f"No filter named '{name}'.", True)
            return

        self.remove(name)
        self.update_filter_list()
        self.show_status(f"Removed filter '{name}'.")

    def on_filter_selected(self):
        item = self.filter_list.currentItem()
        if not item:
            return
        name = item.data(QtCore.Qt.ItemDataRole.UserRole)
        self.name_input.setText(name)

    def add(self, name, filter_type, cutoff_freq, order=4):
        if isinstance(cutoff_freq, (list, tuple)):
            cutoff = cutoff_freq
        else:
            cutoff = float(cutoff_freq)

        sos = signal.butter(order, cutoff, btype=filter_type, fs=self.sample_rate, output='sos')
        self.filters[name] = (sos, filter_type, cutoff, order)

    def remove(self, name):
        if name in self.filters:
            del self.filters[name]

    def apply(self, data):
        for name, (sos, _filter_type, _cutoff, _order) in self.filters.items():
            data = signal.sosfilt(sos, data, axis=0)
        return data
