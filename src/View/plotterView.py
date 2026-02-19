import tkinter as tk
from tkinter import ttk
from Classes.eventClass import *
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)
from matplotlib.figure import Figure
from ViewModel.plotterViewModel import PlotterViewModel
import threading
import queue
import time
import numpy as np

CHOOSE_STREAM = "Choose Stream"
CHOOSE_CHANNEL = "Choose Channel"
MAX_CHANNELS = 4

class PlotterView(EventClass):
    
    def __init__(self, frame: tk.Frame, view_model: PlotterViewModel):
        super().__init__()
        self.frame = frame
        self.view_model = view_model
        
        self.subscribe_to_subject(self.view_model)
        
        self.fig = Figure(figsize=(6, 8), dpi=100)  # taller for multiple plots
        
        
        self.plot_queue = queue.Queue(maxsize=2)  # Small queue to avoid memory buildup
        self.plot_thread = None
        self.stop_thread = threading.Event()

        self._setup_canvas()
        self._setup_controls()
        
        # Start the plotting thread
        self._start_plot_thread()



    def _setup_canvas(self):
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame)
        self.canvas.draw()
        #sorry Kirtana
        #commented out for now because it interferes with the data collection
        #we can get this working later by using the tkinter.focus_set function
        #I don't think this is in use yet -Andy

        #self.canvas.mpl_connect("key_press_event",
                                #lambda event: print(f"you pressed {event.key}"))
        #self.canvas.mpl_connect("key_press_event", key_press_handler)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    


    def _setup_controls(self):
        controls = tk.Frame(self.frame, bd=1, relief=tk.FLAT)
        controls.pack(side=tk.BOTTOM, fill=tk.X, before=self.canvas.get_tk_widget())

        for col in range(6):
            controls.grid_columnconfigure(col, weight=1, uniform="controls")

        self.button_pause = tk.Button(controls, text="Play/Pause", command=self._on_play_pause)
        self.button_pause.grid(row=0, column=0, columnspan=6, padx=6, pady=6, sticky="n")

        self.channel_frame = tk.LabelFrame(controls, text="Selected Channels (Max 4)")
        self.channel_frame.grid(row=2, column=0, columnspan=6, sticky="ew", padx=6)
        self.channel_frame.grid_columnconfigure((0,1,2,3), weight=1)

        self.source_selectors = []

        for i in range(MAX_CHANNELS):
            stream_var = tk.StringVar(value=CHOOSE_STREAM)  # default selection
            channel_var = tk.StringVar(value=CHOOSE_CHANNEL)  # default selection

            ttk.Label(self.channel_frame, text=f"Slot {i+1}").grid(row=i, column=0, padx=4)

            stream_cb = ttk.Combobox(
                self.channel_frame,
                textvariable=stream_var,
                values = [CHOOSE_STREAM] + self.view_model.get_stream_names(),
                state="readonly",
                width=15
            )
            stream_var.set(CHOOSE_STREAM)
            stream_cb.grid(row=i, column=1, padx=4)

            channel_cb = ttk.Combobox(
                self.channel_frame,
                textvariable=channel_var,
                values=[CHOOSE_CHANNEL],  # start with default
                state="readonly",
                width=10
            )
            channel_cb.grid(row=i, column=2, padx=4)

            # Update channels when a stream is selected
            stream_cb.bind(
                "<<ComboboxSelected>>",
                lambda e, sv=stream_var, cv=channel_var: self._update_channel_choices(sv, cv)
            )

            # Update plots when a channel is selected
            channel_cb.bind(
                "<<ComboboxSelected>>",
                lambda e: self._on_source_change()
            )

            self.source_selectors.append({
                "stream_var": stream_var,
                "channel_var": channel_var,
                "stream_cb": stream_cb,
                "channel_cb": channel_cb
            })


        self.toggle_amplitude = tk.Button(controls, text="Hide Amp", command=self._on_toggle_amp)
        self.toggle_amplitude.grid(row=1, column=0, padx=6, pady=6, sticky="ew")

        self.amp_settings = tk.Button(controls, text="Amp Settings", command=lambda: self._open_settings("amplitude"))
        self.amp_settings.grid(row=1, column=1, padx=6, pady=6, sticky="ew")

        self.toggle_power = tk.Button(controls, text="Hide Power", command=self._on_toggle_power_spectrum)
        self.toggle_power.grid(row=1, column=2, padx=6, pady=6, sticky="ew")

        self.power_settings = tk.Button(controls, text="Power Settings", width=15, command=lambda: self._open_settings("power"))
        self.power_settings.grid(row=1, column=3, padx=6, pady=6, sticky="ew")

        self.toggle_bands = tk.Button(controls, text="Hide Band", command=self._on_toggle_band_power)
        self.toggle_bands.grid(row=1, column=4, padx=6, pady=6, sticky="ew")

        self.bands_settings = tk.Button(controls, text="Band Settings", command=lambda: self._open_settings("bands"))
        self.bands_settings.grid(row=1, column=5, padx=6, pady=6, sticky="ew")



    def _update_channel_choices(self, stream_var, channel_var):
        stream_name = stream_var.get()
        
        # If default "Choose Stream" is selected, reset channel
        if stream_name == CHOOSE_STREAM:
            channel_var.set(CHOOSE_CHANNEL)
            for entry in self.source_selectors:
                if entry["stream_var"] is stream_var:
                    entry["channel_cb"]["values"] = [CHOOSE_CHANNEL]
            # Update plot immediately
            self._on_source_change()
            return

        # Normal stream selected
        stream_names = self.view_model.get_stream_names()
        if stream_name not in stream_names:
            return

        stream_idx = stream_names.index(stream_name)
        data = self.view_model._get_data_for_stream(stream_idx)
        if data is None or data.ndim != 2:
            return

        n_ch = data.shape[1]
        channel_choices = [CHOOSE_CHANNEL] + [str(i) for i in range(1, n_ch + 1)]

        for entry in self.source_selectors:
            if entry["stream_var"] is stream_var:
                entry["channel_cb"]["values"] = channel_choices
                # Keep previous selection if valid, else default
                if channel_var.get() not in channel_choices:
                    channel_var.set(CHOOSE_CHANNEL)


    def _on_source_change(self):
        sources = []
        stream_names = self.view_model.get_stream_names()

        for entry in self.source_selectors:
            stream_name = entry["stream_var"].get()
            ch_val = entry["channel_var"].get()

            # Skip slots with default selections
            if stream_name == CHOOSE_STREAM or ch_val == CHOOSE_CHANNEL:
                continue

            if stream_name not in stream_names:
                continue

            try:
                ch_num = int(ch_val)
            except ValueError:
                continue

            stream_idx = stream_names.index(stream_name)
            sources.append((stream_idx, ch_num - 1))

        # Update model with selected sources
        self.view_model.set_selected_sources(sources)

        # Clear any stale plot data in the queue
        with self.plot_queue.mutex:
            self.plot_queue.queue.clear()

        # Force immediate re-render
        plot_data = self.view_model.get_plot_data()
        self._render_plot_data(plot_data)

    
    def _clear_graphs(self):
        """Clear all graph axes and display 'No data'."""
        try:
            self.fig.clear()
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, "No data", ha="center", va="center", fontsize=12)
            ax.set_axis_off()
            self.canvas.draw_idle()
            
        except Exception as e:
            print("[PlotterView] Error clearing graphs:", e)


    def _start_plot_thread(self):
        self.stop_thread.clear()
        self.plot_thread = threading.Thread(target=self._plot_loop, daemon=True)
        self.plot_thread.start()
        # Start the UI update loop
        self._process_plot_queue()

    def _plot_loop(self):
        while not self.stop_thread.is_set():
            if self.view_model.should_continue_plotting():
                try:
                    # Get plot data in background thread
                    plot_data = self.view_model.get_plot_data()
                    
                    # Send to UI thread via queue (non-blocking)
                    try:
                        self.plot_queue.put(plot_data, block=False)
                    except queue.Full:
                        # If queue is full, remove old data and add new
                        try:
                            self.plot_queue.get_nowait()
                            self.plot_queue.put(plot_data, block=False)
                        except:
                            pass
                except Exception as e:
                    print(f"Error in plot loop: {e}")
            
            time.sleep(0.05)

    def _process_plot_queue(self):
        """Process plot data from queue in UI thread - Added: Threading support"""
        try:
            # Check if there's new plot data
            if not self.plot_queue.empty():
                plot_data = self.plot_queue.get_nowait()
                self._render_plot_data(plot_data)
        except queue.Empty:
            pass
        except Exception as e:
            print(f"Error processing plot queue: {e}")
        
        if not self.stop_thread.is_set():
            self.frame.after(50, self._process_plot_queue)

    def _render_plot_data(self, plot_data):
        signals = plot_data.get("signals", [])
        if not plot_data.get("has_data", False):
            self._clear_graphs()
            return
        
        # ---------- PLOTTING ----------
        self.fig.clear()

        if not signals:
            self._show_no_data_message()
        else:
            self._render_plots(plot_data)

        self.fig.tight_layout()
        self.canvas.draw()

 
    def stop(self):
        """Stop the plotting thread - Added: Cleanup method"""
        self.stop_thread.set()
        if self.plot_thread and self.plot_thread.is_alive():
            self.plot_thread.join(timeout=1.0)

    def on_notify(self, eventData, event) -> None:
        if event == EventType.STREAMLISTUPDATE:
            streams = eventData if eventData else []

            # Update each slot's stream dropdown
            for entry in self.source_selectors:
                values = [CHOOSE_STREAM] + streams
                entry["stream_cb"]["values"] = values

                if entry["stream_var"].get() not in values:
                    entry["stream_var"].set(CHOOSE_STREAM)
                    entry["channel_var"].set(CHOOSE_CHANNEL)
                    entry["channel_cb"]["values"] = [CHOOSE_CHANNEL]

  
        elif event == EventType.CLEARALLPLOTS:

            for entry in self.source_selectors:
                entry["stream_cb"]["values"] = [CHOOSE_STREAM]
                entry["stream_var"].set(CHOOSE_STREAM)

                entry["channel_cb"]["values"] = [CHOOSE_CHANNEL]
                entry["channel_var"].set(CHOOSE_CHANNEL)


            self._clear_graphs()

    def _on_play_pause(self):
        is_playing = self.view_model.toggle_plotting()

        if is_playing:
            # Force an immediate plot on PLAY
            self._on_source_change()

            with self.plot_queue.mutex:
                self.plot_queue.queue.clear()
        
        
        self._on_source_change()

        plot_data = self.view_model.get_plot_data()
        self._render_plot_data(plot_data)

        with self.plot_queue.mutex:
            self.plot_queue.queue.clear()

        stream_names = self.view_model.get_stream_names()
 
        for entry in self.source_selectors:
            values = values = [CHOOSE_STREAM] + self.view_model.get_stream_names()
            entry["stream_cb"]["values"] = values

            if entry["stream_var"].get() not in values:
                entry["stream_var"].set(CHOOSE_STREAM)
                entry["channel_var"].set(CHOOSE_CHANNEL)
                entry["channel_cb"]["values"] = [CHOOSE_CHANNEL]

        slot_idx = 0

        for stream_idx, stream_name in enumerate(stream_names):
            if slot_idx >= len(self.source_selectors):
                break

            data = self.view_model._get_data_for_stream(stream_idx)
            if data is None or data.ndim != 2:
                continue

            n_ch = data.shape[1]

            for ch in range(n_ch):
                if slot_idx >= len(self.source_selectors):
                    break

                entry = self.source_selectors[slot_idx]

                # Skip already-filled slots
                if entry["stream_var"].get() != CHOOSE_STREAM:
                    continue
                entry["stream_var"].set(stream_name)

                slot_idx += 1

        self._on_source_change()
        for entry in self.source_selectors:
            if entry["stream_var"].get() and not entry["channel_cb"]["values"]:
                self._update_channel_choices(entry["stream_var"], entry["channel_var"])

    def _on_toggle_amp(self):
        show_amplitude = self.view_model.toggle_amplitude()
        self.toggle_amplitude.config(text="Hide Amp" if show_amplitude else "Show Amp")

    def _on_toggle_power_spectrum(self):
        show_power = self.view_model.toggle_power_spectrum()
        self.toggle_power.config(text="Hide Power" if show_power else "Show Power")

    def _on_toggle_band_power(self):
        show_bands = self.view_model.toggle_band_power()
        self.toggle_bands.config(text="Hide Band" if show_bands else "Show Band")

    def _open_settings(self, graph_type):
        """Open settings popup - Fixed: Access labels directly without calling get_plot_data()"""
        popup = tk.Toplevel(self.frame)
        popup.title(f"{graph_type.capitalize()} Settings")

        current_labels = self.view_model.labels[graph_type]

        tk.Label(popup, text="Graph Title:").grid(row=0, column=0, sticky="w")
        title_entry = tk.Entry(popup)
        title_entry.insert(0, current_labels["title"])
        title_entry.grid(row=0, column=1)

        tk.Label(popup, text="X-axis Label:").grid(row=1, column=0, sticky="w")
        xlabel_entry = tk.Entry(popup)
        xlabel_entry.insert(0, current_labels["xlabel"])
        xlabel_entry.grid(row=1, column=1)

        tk.Label(popup, text="Y-axis Label:").grid(row=2, column=0, sticky="w")
        ylabel_entry = tk.Entry(popup)
        ylabel_entry.insert(0, current_labels["ylabel"])
        ylabel_entry.grid(row=2, column=1)

        if graph_type == "bands":
            tk.Label(popup, text="Visible Bands:", font=("Arial", 10, "bold")).grid(
                row=3, column=0, columnspan=2, pady=(10, 4), sticky="w"
            )

            band_vars = {}
            visibility = self.view_model.get_band_visibility()

            row = 4
            for band, is_visible in visibility.items():
                var = tk.BooleanVar(value=is_visible)
                band_vars[band] = var
                tk.Checkbutton(popup, text=band, variable=var).grid(
                    row=row, column=0, columnspan=2, sticky="w"
                )
                row += 1

        def apply_settings():
            self.view_model.update_labels(
                graph_type,
                title_entry.get(),
                xlabel_entry.get(),
                ylabel_entry.get()
            )

            if graph_type == "bands":
                for band, var in band_vars.items():
                    self.view_model.set_band_visibility(band, var.get())

            popup.destroy()


        apply_row = row if graph_type == "bands" else 3

        tk.Button(
            popup,
            text="Apply",
            command=apply_settings
        ).grid(row=apply_row, column=0, columnspan=2, pady=8)

    def plot(self):
        # This method is no longer used - thread handles all plotting
        pass

    def _show_no_data_message(self):
        ax = self.fig.add_subplot(111)
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        ax.set_axis_off()

    def _render_plots(self, plot_data):
        if plot_data['n_subplots'] == 0:
            self._show_no_data_message()
            return

        signals = plot_data['signals']
        time_axes = plot_data['time_axes']

        subplot_index = 1

        # -------- AMPLITUDE --------
        if plot_data['show_amplitude']:
            ax = self.fig.add_subplot(plot_data['n_subplots'], 1, subplot_index)
            for sig, t, (stream_idx, ch_idx) in zip(
                    signals,
                    plot_data["time_axes"],
                    plot_data["sources"]
            ):
                stream_name = self.view_model.get_stream_names()[stream_idx]
                ax.plot(t, sig, label=f"{stream_name} · Ch {ch_idx + 1}")


            ax.set_title(plot_data['labels']['amplitude']['title'])
            ax.set_xlabel(plot_data['labels']['amplitude']['xlabel'])
            ax.set_ylabel(plot_data['labels']['amplitude']['ylabel'])
            ax.legend(
                loc="upper right",
                fontsize=8,
                frameon=True,
                framealpha=0.5,
                handlelength=1.2,
                handletextpad=0.4,
                labelspacing=0.3,
                borderpad=0.3
            )

            subplot_index += 1

        # -------- POWER SPECTRUM --------
        if plot_data['show_power']:
            ax = self.fig.add_subplot(plot_data['n_subplots'], 1, subplot_index)

            for psd, freqs, (stream_idx, ch_idx) in zip(
                plot_data["psds"],
                plot_data["freqs_list"],
                plot_data["sources"]
            ):
                n = min(len(psd), len(freqs))
                ax.plot(
                    freqs[:n],
                    psd[:n],
                    label=f"{self.view_model.get_stream_names()[stream_idx]} · Ch {ch_idx + 1}"
                )

            ax.set_title(plot_data['labels']['power']['title'])
            ax.set_xlabel(plot_data['labels']['power']['xlabel'])
            ax.set_ylabel(plot_data['labels']['power']['ylabel'])

            subplot_index += 1


        # -------- BAND POWERS --------
        if plot_data['show_bands']:
            ax = self.fig.add_subplot(plot_data['n_subplots'], 1, subplot_index)

            band_labels = plot_data['band_labels']
            band_powers = np.array(plot_data['band_powers'])  # shape: (n_channels, n_bands)
            n_channels, n_bands = band_powers.shape

            x = np.arange(n_bands)  # band positions
            total_width = 0.8
            bar_width = total_width / n_channels

            for i, (stream_idx, ch_idx) in enumerate(plot_data["sources"]):
                stream_name = self.view_model.get_stream_names()[stream_idx]
                ax.bar(
                    x + i * bar_width,
                    band_powers[i],
                    width=bar_width,
                    label=f"{stream_name} · Ch {ch_idx + 1}"
    )

            ax.set_xticks(x + total_width / 2 - bar_width / 2)
            ax.set_xticklabels(band_labels)

            ax.set_title(plot_data['labels']['bands']['title'])
            ax.set_xlabel(plot_data['labels']['bands']['xlabel'])
            ax.set_ylabel(plot_data['labels']['bands']['ylabel'])


# Changed: Factory function to create both ViewModel and View together
def create_plotter(frame: tk.Frame, user_model):
    """Factory function to create a complete plotter with ViewModel and View"""
    view_model = PlotterViewModel(user_model)
    view = PlotterView(frame, view_model)
    return view_model, view