import tkinter as tk
import numpy as np

# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)
from matplotlib.figure import Figure
from userModel import UserModel
from dataStream import StreamType


class Plotter():
    def __init__(self, frame: tk.Frame, user_model: UserModel):
        self.user_model = user_model
        self.frame = frame
        self.fig = Figure(figsize=(6, 8), dpi=100)  # taller for multiple plots
        self.continue_plotting = True
        self.simulated = False

        # --- Get available streams ---
        if self.simulated:
            # Simulated 4 "streams" with different frequencies
            self.streams = ["SimStream1", "SimStream2", "SimStream3", "SimStream4"]
        else:
            self.streams = [s for s in self.user_model.get_streams()]

        self.current_stream_index = 0
        self.stream_names = [f"Stream {i+1}" for i in range(len(self.streams))]


        # embed Matplotlib in Tk
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas.draw()
        self.canvas.mpl_connect("key_press_event",
                                lambda event: print(f"you pressed {event.key}"))
        self.canvas.mpl_connect("key_press_event", key_press_handler)

        # Buttons
        controls = tk.Frame(frame)
        controls.pack(side=tk.BOTTOM, fill=tk.X)

        self.button_pause = tk.Button(controls, text="Play/Pause", command=self.play_pause)
        self.button_pause.pack(side=tk.BOTTOM)

        self.selected_stream = tk.StringVar(value=self.stream_names[0])
        self.stream_menu = tk.OptionMenu(controls, self.selected_stream, *self.stream_names, command=self.change_stream)
        self.stream_menu.pack(side=tk.LEFT, padx=5, pady=5)

        self.toggle_amplitude = tk.Button(controls, text="Hide Amplitude", command=self.toggle_amp)
        self.toggle_amplitude.pack(side=tk.LEFT, padx=5, pady = 5)

        self.amp_settings = tk.Button(controls, text="Amplitude Settings", command=lambda: self.open_settings("amplitude"))
        self.amp_settings.pack(side=tk.LEFT)

        self.toggle_power = tk.Button(controls, text="Hide Power Spectrum", command=self.toggle_power_spectrum)
        self.toggle_power.pack(side=tk.LEFT)

        self.power_settings = tk.Button(controls, text="Power Settings", command=lambda: self.open_settings("power"))
        self.power_settings.pack(side=tk.LEFT)

        self.toggle_bands = tk.Button(controls, text="Hide Band Power", command=self.toggle_band_power)
        self.toggle_bands.pack(side=tk.LEFT)

        self.bands_settings = tk.Button(controls, text="Band Settings", command=lambda: self.open_settings("bands"))
        self.bands_settings.pack(side=tk.LEFT)

        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # EEG frequency bands
        self.bands = {
            "delta (0.5–4 Hz)": (0.5, 4),
            "theta (4–8 Hz)": (4, 8),
            "alpha (8–13 Hz)": (8, 13),
            "beta (13–30 Hz)": (13, 30),
            "gamma (30–45 Hz)": (30, 45),
        }

        # Visibility flags
        self.show_amplitude = True
        self.show_power = True
        self.show_bands = True

        # Label settings (user editable)
        self.labels = {
            "amplitude": {"title": "Amplitude vs Time", "xlabel": "Time (s)", "ylabel": "Amplitude (µV)"},
            "power": {"title": "Power Spectrum", "xlabel": "Frequency (Hz)", "ylabel": "Power"},
            "bands": {"title": "Band Power", "xlabel": "Band", "ylabel": "Power"},
        }

        self.plot()

    def play_pause(self):
        if not self.continue_plotting:
            self.continue_plotting = not self.continue_plotting
            self.plot()
        else:
            self.continue_plotting = not self.continue_plotting
    
    def change_stream(self, selection):
        """Switch which stream is plotted."""
        self.current_stream_index = self.stream_names.index(selection)
        self.plot() #force redraw

    def toggle_amp(self):
        self.show_amplitude = not self.show_amplitude
        self.toggle_amplitude.config(text="Show Amplitude" if not self.show_amplitude else "Hide Amplitude")

    def toggle_power_spectrum(self):
        self.show_power = not self.show_power
        self.toggle_power.config(text="Show Power Spectrum" if not self.show_power else "Hide Power Spectrum")

    def toggle_band_power(self):
        self.show_bands = not self.show_bands
        self.toggle_bands.config(text="Show Band Power" if not self.show_bands else "Hide Band Power")

    def open_settings(self, graph_type):
        """Open a popup window to edit title, xlabel, ylabel."""
        popup = tk.Toplevel(self.frame)
        popup.title(f"{graph_type.capitalize()} Settings")

        tk.Label(popup, text="Graph Title:").grid(row=0, column=0, sticky="w")
        title_entry = tk.Entry(popup)
        title_entry.insert(0, self.labels[graph_type]["title"])
        title_entry.grid(row=0, column=1)

        tk.Label(popup, text="X-axis Label:").grid(row=1, column=0, sticky="w")
        xlabel_entry = tk.Entry(popup)
        xlabel_entry.insert(0, self.labels[graph_type]["xlabel"])
        xlabel_entry.grid(row=1, column=1)

        tk.Label(popup, text="Y-axis Label:").grid(row=2, column=0, sticky="w")
        ylabel_entry = tk.Entry(popup)
        ylabel_entry.insert(0, self.labels[graph_type]["ylabel"])
        ylabel_entry.grid(row=2, column=1)

        def apply_settings():
            self.labels[graph_type]["title"] = title_entry.get()
            self.labels[graph_type]["xlabel"] = xlabel_entry.get()
            self.labels[graph_type]["ylabel"] = ylabel_entry.get()
            popup.destroy()

        tk.Button(popup, text="Apply", command=apply_settings).grid(row=3, column=0, columnspan=2)

    def plot(self):
        """Plot amplitude vs time, power spectrum, and band powers."""

        # pull data from user_model streams
        if self.simulated:
        # generate fake data
            fs = 250
            t = np.linspace(0, 2, 2*fs, endpoint=False)
            if self.current_stream_index == 0:
                data = 50*np.sin(2*np.pi*10*t) + 10*np.random.randn(len(t))
            elif self.current_stream_index == 1:
                data = 40*np.sin(2*np.pi*6*t) + 15*np.random.randn(len(t))
            elif self.current_stream_index == 2:
                data = 30*np.sin(2*np.pi*20*t) + 10*np.random.randn(len(t))
            else:
                data = 20*np.sin(2*np.pi*30*t) + 10*np.random.randn(len(t))
        else:
            data = []
            if self.streams:
                data = list(self.streams[self.current_stream_index].get_stream())

        self.fig.clear()  # clear figure before redrawing

        if len(data) > 0:
            data = np.array(data)
            fs = 250  # assume 250 Hz sampling

            subplot_index = 1
            n_subplots = sum([self.show_amplitude, self.show_power, self.show_bands])

            if self.show_amplitude:
                ax1 = self.fig.add_subplot(n_subplots, 1, subplot_index)
                subplot_index += 1
                time_axis = np.arange(len(data)) / fs
                ax1.plot(time_axis, data, color="blue")
                
                ax1.set_title(self.labels["amplitude"]["title"])
                ax1.set_ylabel(self.labels["amplitude"]["ylabel"])
                ax1.set_xlabel(self.labels["amplitude"]["xlabel"])
                ax1.set_ylim([-100, 100])

            if self.show_power:
                freqs = np.fft.rfftfreq(len(data), 1 / fs)
                psd = np.abs(np.fft.rfft(data)) ** 2
                ax2 = self.fig.add_subplot(n_subplots, 1, subplot_index)
                subplot_index += 1
                ax2.plot(freqs, psd, color="green")
                ax2.set_xlim([0, 50])  # up to 50 Hz
                ax2.set_title(self.labels["power"]["title"])
                ax2.set_xlabel(self.labels["power"]["xlabel"])
                ax2.set_ylabel(self.labels["power"]["ylabel"])

            if self.show_bands:
                freqs = np.fft.rfftfreq(len(data), 1 / fs)
                psd = np.abs(np.fft.rfft(data)) ** 2
                band_powers = []
                labels = []
                for band, (low, high) in self.bands.items():
                    idx = np.logical_and(freqs >= low, freqs <= high)
                    band_powers.append(psd[idx].mean())
                    labels.append(band)

                ax3 = self.fig.add_subplot(n_subplots, 1, subplot_index)
                ax3.bar(labels, band_powers, color="orange")
                ax3.set_title(self.labels["bands"]["title"])
                ax3.set_xlabel(self.labels["bands"]["xlabel"])
                ax3.set_ylabel(self.labels["bands"]["ylabel"])
                ax3.tick_params(axis='x', rotation=30)    

        else:
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, "No data", ha="center", va="center")
            ax.set_axis_off()

        # refresh canvas
        self.fig.tight_layout()
        self.canvas.draw()
        self.canvas.flush_events()

        # schedule next update
        if self.continue_plotting:
            self.frame.after(10, self.plot)  


