import numpy as np
from eventClass import *
from userModel import UserModel
from dataStream import StreamType


class PlotterViewModel(EventClass):
    def __init__(self, user_model: UserModel):
        super().__init__()
        self.user_model = user_model
        self.continue_plotting = True
        self.simulated = True  # Changed: Moved simulation flag to ViewModel as it's business logic

        self.subscribe_to_subject(self.user_model)

        # --- Get available streams ---
        if self.simulated:
            # Simulated 4 "streams" with different frequencies
            self.streams = ["SimStream1", "SimStream2", "SimStream3", "SimStream4"]
        else:
            self.streams = [s for s in self.user_model.get_streams() if s.stream_type in [StreamType.FILTER, StreamType.DEVICE, StreamType.SOFTWARE]]

        self.current_stream_index = 0
        self.stream_names = [f"Stream {i+1}" for i in range(len(self.streams))]

        # EEG frequency bands - Changed: Moved to ViewModel as it's domain logic
        self.bands = {
            "delta (0.5–4 Hz)": (0.5, 4),
            "theta (4–8 Hz)": (4, 8),
            "alpha (8–13 Hz)": (8, 13),
            "beta (13–30 Hz)": (13, 30),
            "gamma (30–45 Hz)": (30, 45),
        }

        # Visibility flags - Changed: Moved to ViewModel to manage state
        self.show_amplitude = True
        self.show_power = True
        self.show_bands = True

        # Label settings (user editable) - Changed: Moved to ViewModel as it's configuration data
        self.labels = {
            "amplitude": {"title": "Amplitude vs Time", "xlabel": "Time (s)", "ylabel": "Amplitude (µV)"},
            "power": {"title": "Power Spectrum", "xlabel": "Frequency (Hz)", "ylabel": "Power"},
            "bands": {"title": "Band Power", "xlabel": "Band", "ylabel": "Power"},
        }

    def refresh_stream_list(self):
        """Refresh the list of available streams - Changed: Pure business logic, stays in ViewModel"""
        self.streams = [s for s in self.user_model.get_streams() if s.stream_type in [StreamType.FILTER, StreamType.DEVICE, StreamType.SOFTWARE]]
        self.stream_names = [f"Stream {i+1}" for i in range(len(self.streams))]
        return self.stream_names

    def on_notify(self, eventData, event) -> None:
        """Handle events from the user model - Changed: Business logic, stays in ViewModel"""
        if event == EventType.DEVICELISTUPDATE:
            self.refresh_stream_list()
            # Changed: Notify View about stream list update
            self.notify_subscribers(EventType.STREAMLISTUPDATE, self.stream_names)
            
    def toggle_plotting(self):
        """Toggle the plotting state - Changed: Business logic method"""
        if not self.continue_plotting:
            self.continue_plotting = not self.continue_plotting
            return True  # Should start plotting
        else:
            self.continue_plotting = not self.continue_plotting
            return False  # Should stop plotting
    
    def change_stream(self, selection):
        """Change the current stream - Changed: Business logic, returns success status"""
        if selection in self.stream_names:
            self.current_stream_index = self.stream_names.index(selection)
            return True
        return False

    def toggle_amplitude(self):
        """Toggle amplitude visibility - Changed: Returns new state for View to update UI"""
        self.show_amplitude = not self.show_amplitude
        return self.show_amplitude

    def toggle_power_spectrum(self):
        """Toggle power spectrum visibility - Changed: Returns new state for View to update UI"""
        self.show_power = not self.show_power
        return self.show_power

    def toggle_band_power(self):
        """Toggle band power visibility - Changed: Returns new state for View to update UI"""
        self.show_bands = not self.show_bands
        return self.show_bands

    def update_labels(self, graph_type, title, xlabel, ylabel):
        """Update labels for a specific graph type - Changed: Business logic for managing labels"""
        if graph_type in self.labels:
            self.labels[graph_type]["title"] = title
            self.labels[graph_type]["xlabel"] = xlabel
            self.labels[graph_type]["ylabel"] = ylabel
            return True
        return False

    def get_plot_data(self):
        """Get all data needed for plotting - Changed: Central method to provide all plotting data to View"""
        # Generate or get data
        if self.simulated:
            data = self._generate_simulated_data()
        else:
            data = self._get_real_data()

        if len(data) == 0:
            return {
                'has_data': False,
                'data': [],
                'time_axis': [],
                'freqs': [],
                'psd': [],
                'band_powers': [],
                'band_labels': [],
                'n_subplots': 0
            }

        data = np.array(data)
        fs = 250  # assume 250 Hz sampling
        
        # Calculate time axis
        time_axis = np.arange(len(data)) / fs
        
        # Calculate power spectrum
        freqs = np.fft.rfftfreq(len(data), 1 / fs)
        psd = np.abs(np.fft.rfft(data)) ** 2
        
        # Calculate band powers
        band_powers = []
        band_labels = []
        for band, (low, high) in self.bands.items():
            idx = np.logical_and(freqs >= low, freqs <= high)
            band_powers.append(psd[idx].mean())
            band_labels.append(band)

        n_subplots = sum([self.show_amplitude, self.show_power, self.show_bands])

        return {
            'has_data': True,
            'data': data,
            'time_axis': time_axis,
            'freqs': freqs,
            'psd': psd,
            'band_powers': band_powers,
            'band_labels': band_labels,
            'n_subplots': n_subplots,
            'labels': self.labels,
            'show_amplitude': self.show_amplitude,
            'show_power': self.show_power,
            'show_bands': self.show_bands
        }

    def _generate_simulated_data(self):
        """Generate simulated data - Changed: Private method for data generation logic"""
        fs = 250
        t = np.linspace(0, 2, 2*fs, endpoint=False)
        if self.current_stream_index == 0:
            return 50*np.sin(2*np.pi*10*t) + 10*np.random.randn(len(t))
        elif self.current_stream_index == 1:
            return 40*np.sin(2*np.pi*6*t) + 15*np.random.randn(len(t))
        elif self.current_stream_index == 2:
            return 30*np.sin(2*np.pi*20*t) + 10*np.random.randn(len(t))
        else:
            return 20*np.sin(2*np.pi*30*t) + 10*np.random.randn(len(t))

    def _get_real_data(self):
        """Get real data from streams - Changed: Private method for real data access"""
        data = []
        if self.streams and self.current_stream_index < len(self.streams):
            data = list(self.streams[self.current_stream_index].get_stream_data())
        return data

    def should_continue_plotting(self):
        """Check if plotting should continue - Changed: Simple state accessor for View"""
        return self.continue_plotting

    def get_stream_names(self):
        """Get current stream names - Changed: Accessor method for View"""
        return self.stream_names

    def get_current_stream_name(self):
        """Get currently selected stream name - Changed: Accessor method for View"""
        if self.current_stream_index < len(self.stream_names):
            return self.stream_names[self.current_stream_index]
        return ""