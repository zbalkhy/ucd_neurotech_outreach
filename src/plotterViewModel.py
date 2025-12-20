import numpy as np
from eventClass import *
from userModel import UserModel
from dataStream import DataStream, StreamType


class PlotterViewModel(EventClass):
    def __init__(self, user_model: UserModel):
        super().__init__()
        self._stream_version = 0
        self.selected_channels = []  # list of 0-based channel indices
        self.max_visible_channels = 4


        self.user_model = user_model
        self.continue_plotting = True
        self.simulated = False
        

        self.subscribe_to_subject(self.user_model)

        # --- Get available streams ---
        if self.simulated:
            # Simulated 4 "streams" with different frequencies
            types = [StreamType.FILTER, StreamType.DEVICE, StreamType.SOFTWARE]
            self.streams = [
                DataStream(stream_name=f"SimStream{i+1}", stream_type=types[i % len(types)])
                for i in range(4)
            ]
        else:
            self.streams = [s for s in self.user_model.get_streams() if s.stream_type in [StreamType.FILTER, StreamType.DEVICE, StreamType.SOFTWARE]]
        
        # Track user-defined names separately
        self.custom_names = {}

        self.stream_names = [self._get_display_name(s) for s in self.streams]
        self.current_stream_index = 0

        # EEG frequency bands 
        self.bands = {
            "delta (0.5–4 Hz)": (0.5, 4),
            "theta (4–8 Hz)": (4, 8),
            "alpha (8–13 Hz)": (8, 13),
            "beta (13–30 Hz)": (13, 30),
            "gamma (30–45 Hz)": (30, 45),
        }

        self.band_visibility = {
            "delta (0.5–4 Hz)": True,
            "theta (4–8 Hz)": True,
            "alpha (8–13 Hz)": True,
            "beta (13–30 Hz)": True,
            "gamma (30–45 Hz)": True,
        }

        
        self.show_amplitude = True
        self.show_power = True
        self.show_bands = True

        
        self.labels = {
            "amplitude": {"title": "Amplitude vs Time", "xlabel": "Time (s)", "ylabel": "Amplitude (µV)"},
            "power": {"title": "Power Spectrum", "xlabel": "Frequency (Hz)", "ylabel": "Power"},
            "bands": {"title": "Band Power", "xlabel": "Band", "ylabel": "Power"},
        }
    
        
    def get_channel_count(self):
        if self.simulated:
            data = self._generate_simulated_data()
        else:
            data = self._get_real_data()

        if isinstance(data, np.ndarray) and data.ndim == 2:
            return data.shape[1]
        return 1

    def _default_selected_channels(self, n_channels):
        return list(range(min(self.max_visible_channels, n_channels)))
    
    def set_selected_channels(self, channels):
        """channels: list of 0-based indices"""
        n_channels = self.get_channel_count()
        self.selected_channels = [
            ch for ch in channels
            if 0 <= ch < n_channels
        ][:self.max_visible_channels]

    def get_selected_channels(self):
        return list(self.selected_channels)



    def _get_display_name(self, stream):
        """Return user-customized name if available, else inherent name."""
        inherent = getattr(stream, "stream_name", None) or "UnnamedStream"
        return self.custom_names.get(inherent, inherent)

    def rename_stream(self, display_name, new_name):
        """
        Rename the stream with current display_name to new_name.
        Keys custom_names by the inherent streamname.
        Returns True if rename succeeded, False otherwise.
        """
        for stream in self.streams:
            inherent = getattr(stream, "stream_name", None)
            if inherent is None:
                continue
            current_display = self.custom_names.get(inherent, inherent)
            if current_display == display_name:
                # set new custom name 
                self.custom_names[inherent] = new_name
                # refresh stream_names and notify UI
                self.stream_names = [self._get_display_name(s) for s in self.streams]
                self.notify_subscribers(EventType.STREAMLISTUPDATE, self.stream_names)
                return True
        return False

    def delete_stream_by_name(self, display_name):
        """Delete a stream (simulated or real) by its display name."""
        inherent_name = self.get_inherent_name(display_name) or display_name

        #  Find and remove stream 
        target = None
        for s in list(self.streams):
            if getattr(s, "stream_name", None) == inherent_name:
                target = s
                break

        if not target:
            print(f"No stream found to delete: {inherent_name}")
            return False

        # Stop the stream safely
        try:
            target.shutdown_event.set()
            if target.is_alive():
                target.join(timeout=0.5)
        except Exception as e:
            print(f"[PlotterViewModel] Warning stopping stream {inherent_name}: {e}")

        # Remove from internal list
        self.streams.remove(target)

        # Remove from custom name map
        if inherent_name in self.custom_names:
            del self.custom_names[inherent_name]

        # --- Update user_model if not simulated ---
        if not self.simulated:
            try:
                if hasattr(self.user_model, "remove_stream_by_name"):
                    self.user_model.remove_stream_by_name(inherent_name)
                    print(f"[PlotterViewModel] Removed '{inherent_name}' from user_model.")
                else:
                    print("[PlotterViewModel] WARNING: user_model missing remove_stream_by_name()")
            except Exception as e:
                print(f"[PlotterViewModel] Error removing from user_model: {e}")

        # --- Refresh internal state and notify UI ---
        self.stream_names = [self._get_display_name(s) for s in self.streams]
        self.notify_subscribers(EventType.STREAMLISTUPDATE, self.stream_names)

        # If the deleted stream was the one currently shown, adjust index
        if self.current_stream_index >= len(self.streams):
            self.current_stream_index = max(0, len(self.streams) - 1)

        # If no streams left, signal the view to clear all plots
        if not self.streams:
            self.notify_subscribers(EventType.CLEARALLPLOTS, None)

        return True
        

    def refresh_stream_list(self):
        if not self.simulated:
            self.streams = [
                s for s in self.user_model.get_streams()
                if s.stream_type in [StreamType.FILTER, StreamType.DEVICE, StreamType.SOFTWARE]
            ]
        self.stream_names = [self._get_display_name(s) for s in self.streams]
        return self.stream_names

    def on_notify(self, eventData, event) -> None:
        if event == EventType.STREAMUPDATE:
            self.refresh_stream_list()
            self.notify(self.stream_names, EventType.STREAMLISTUPDATE)

    def toggle_plotting(self):
        if not self.continue_plotting:
            self.continue_plotting = not self.continue_plotting
            return True  # Should start plotting
        else:
            self.continue_plotting = not self.continue_plotting
            return False  # Should stop plotting
    
    def change_stream(self, selection):
        if selection in self.stream_names:
            self.current_stream_index = self.stream_names.index(selection)

            # Clamp channel index to new stream's channel count
            # Reset channel selection for new stream
            n_ch = self.get_channel_count()
            self.selected_channels = self._default_selected_channels(n_ch)

            self._stream_version += 1

            return True
        return False

    def toggle_amplitude(self):
        self.show_amplitude = not self.show_amplitude
        return self.show_amplitude

    def toggle_power_spectrum(self):
        self.show_power = not self.show_power
        return self.show_power

    def toggle_band_power(self):
        self.show_bands = not self.show_bands
        return self.show_bands

    def set_band_visibility(self, band_name: str, visible: bool):
        if band_name in self.band_visibility:
            self.band_visibility[band_name] = visible

    def get_band_visibility(self):
        return dict(self.band_visibility)

    def update_labels(self, graph_type, title, xlabel, ylabel):
        if graph_type in self.labels:
            self.labels[graph_type]["title"] = title
            self.labels[graph_type]["xlabel"] = xlabel
            self.labels[graph_type]["ylabel"] = ylabel
            return True
        return False
    

    def get_plot_data(self):
        if self.simulated:
            data = self._generate_simulated_data()
        else:
            data = self._get_real_data()

        if data is None or data.size == 0:
            return {
                'has_data': False,
                'signals': [],
                'n_channels': 0
            }

        data = np.asarray(data)

        if data.ndim == 1:
            signals = [data]
            channel_indices = [0]
            n_channels = 1
            self.selected_channels = [0]

        elif data.ndim == 2:
            n_channels = data.shape[1]

            # Initialize defaults if empty or invalid
            if not self.selected_channels:
                self.selected_channels = self._default_selected_channels(n_channels)

            # Clamp to available channels
            self.selected_channels = [
                ch for ch in self.selected_channels if ch < n_channels
            ]

            signals = [data[:, ch] for ch in self.selected_channels]
            channel_indices = list(self.selected_channels)

        else:
            return {'has_data': False}


        fs = 250
        time_axis = np.arange(len(signals[0])) / fs

        # ---------- POWER SPECTRA (PER CHANNEL) ----------
        freqs = np.fft.rfftfreq(len(signals[0]), 1 / fs)
        psds = [
            np.abs(np.fft.rfft(sig)) ** 2
            for sig in signals
        ]

        # ---------- BAND POWERS (PER CHANNEL) ----------
        band_labels = []
        band_powers = []  # shape: [n_channels_shown, n_bands]

        for band, (low, high) in self.bands.items():
            if not self.band_visibility.get(band, True):
                continue

            band_labels.append(band)

            idx = (freqs >= low) & (freqs <= high)

            band_values_per_channel = []
            for psd in psds:
                if np.any(idx):
                    band_values_per_channel.append(psd[idx].mean())
                else:
                    band_values_per_channel.append(0.0)

            band_powers.append(band_values_per_channel)

        # transpose → channels x bands
        band_powers = np.array(band_powers).T


        return {
            'has_data': True,
            'signals': signals,
            'channel_indices': channel_indices,
            'time_axis': time_axis,
            'freqs': freqs,
            'psds': psds,
            'band_powers': band_powers,
            'band_labels': band_labels,
            'n_channels': n_channels,
            'n_subplots': sum([
                self.show_amplitude,
                self.show_power,
                self.show_bands
            ]),
            'labels': self.labels,
            'show_amplitude': self.show_amplitude,
            'show_power': self.show_power,
            'show_bands': self.show_bands,
        }






    def _generate_simulated_data(self):
        fs = 250
        t = np.linspace(0, 2, 2*fs, endpoint=False)

        if not self.streams or self.current_stream_index >= len(self.streams):
            # No streams left — return empty 2D array
            return np.empty((0, 1))

        # Identify stream uniquely by its name
        stream_name = getattr(self.streams[self.current_stream_index], "stream_name", "")

        # Assign frequency, amplitude, noise, and number of channels based on stream
        if "SimStream1" in stream_name:
            freq, amp, noise, n_ch = 10, 50, 10, 8
        elif "SimStream2" in stream_name:
            freq, amp, noise, n_ch = 6, 40, 15, 5
        elif "SimStream3" in stream_name:
            freq, amp, noise, n_ch = 20, 30, 10, 2
        elif "SimStream4" in stream_name:
            freq, amp, noise, n_ch = 30, 20, 10, 1
        else:
            freq, amp, noise, n_ch = 8, 25, 10, 1

        # Generate multi-channel signal
        channels = np.stack([
            amp * np.sin(2 * np.pi * (freq + i) * t) + noise * np.random.randn(len(t))
            for i in range(n_ch)
        ], axis=1)

        return channels  # Return full multi-channel array

        
    def _get_real_data(self):
        if not self.streams or self.current_stream_index >= len(self.streams):
            print("No streams or invalid index")
            return np.array([])

        raw = self.streams[self.current_stream_index].get_stream_data()

        if raw is None:
            return np.array([])

        if isinstance(raw, deque) and len(raw) == 0:
            return np.array([])
        data = np.asarray(raw)
        return data

    

    def should_continue_plotting(self):
        return self.continue_plotting

    def get_stream_names(self):
        """Return the current list of display names (custom or inherent)."""
        # keep stream_names in sync with streams/custom_names
        self.stream_names = [self._get_display_name(s) for s in self.streams]
        return self.stream_names

    def get_current_stream_name(self):
        """Return the display name for the currently selected stream index."""
        if 0 <= self.current_stream_index < len(self.streams):
            return self._get_display_name(self.streams[self.current_stream_index])
        return ""
    
    def get_inherent_name(self, display_name):
        """Given a display name (possibly user-customized), return the inherent streamname."""
        for stream in self.streams:
            inherent = getattr(stream, "stream_name", None)
            if inherent is None:
                continue
            current_display = self.custom_names.get(inherent, inherent)
            if current_display == display_name:
                return inherent
        return None