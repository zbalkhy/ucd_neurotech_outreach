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
        self._channel_cache = {}  # stream_idx → n_channels
        self._manual_limits = {
            "amplitude": {"x": None, "y_min": None, "y_max": None},
            "power":     {"x": None, "y_min": None, "y_max": None},
            "bands":     {"x": None, "y_min": None, "y_max": None},
        }
        self._y_limits = {
            "amplitude": [None, None],
            "power":     [None, None],
            "bands":     [None, None],
        }
        self._pending_ylimits = {}  # graph_type -> (ax, y_lo, y_hi)

        self.fig = Figure(figsize=(6, 8), dpi=100)

        self.plot_queue = queue.Queue(maxsize=2)
        self.plot_thread = None
        self.stop_thread = threading.Event()

        self._setup_canvas()
        self._setup_controls()
        self._start_plot_thread()
        self._start_channel_state_updater()

    def _setup_canvas(self):
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame)
        self.canvas.draw()
        self.canvas.mpl_connect(
            "key_press_event",
            lambda event: print(
                f"you pressed {event.key}"))
        self.canvas.mpl_connect("key_press_event", key_press_handler)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def _setup_controls(self):
        controls = tk.Frame(self.frame, bd=1, relief=tk.FLAT)
        TOTAL_COLS = 12
        for col in range(TOTAL_COLS):
            controls.grid_columnconfigure(col, weight=1)
        controls.pack(side=tk.BOTTOM, fill=tk.X,
                      before=self.canvas.get_tk_widget())

        self.channel_frame = tk.LabelFrame(controls, text="Selected Channels")
        self.channel_frame.grid(
            row=2, column=0, columnspan=12, sticky="ew", padx=6)
        self.channel_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.source_selectors = []
        slot_count = self.view_model.max_visible_channels

        for i in range(slot_count):
            stream_var = tk.StringVar(value=CHOOSE_STREAM)
            channel_var = tk.StringVar(value=CHOOSE_CHANNEL)

            ttk.Label(self.channel_frame,
                      text=f"Slot {i + 1}").grid(row=i, column=0, padx=4)

            stream_cb = ttk.Combobox(
                self.channel_frame,
                textvariable=stream_var,
                values=[CHOOSE_STREAM] + self.view_model.get_stream_names(),
                state="readonly",
                width=15
            )
            stream_var.set(CHOOSE_STREAM)
            stream_cb.grid(row=i, column=1, padx=4)

            channel_cb = ttk.Combobox(
                self.channel_frame,
                textvariable=channel_var,
                values=[CHOOSE_CHANNEL],
                state="readonly",
                width=10
            )
            channel_cb.grid(row=i, column=2, padx=4)

            stream_cb.bind(
                "<<ComboboxSelected>>",
                lambda e, sv=stream_var, cv=channel_var: self._update_channel_choices(sv, cv))

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

        buttons = []

        if self.view_model.allow_amplitude_plot:
            self.toggle_amplitude = tk.Button(
                controls, text="Hide Amp", command=self._on_toggle_amp)
            buttons.append(self.toggle_amplitude)

        if self.view_model.allow_amp_settings:
            self.amp_settings = tk.Button(
                controls, text="Amp Settings",
                command=lambda: self._open_settings("amplitude"))
            buttons.append(self.amp_settings)

        if self.view_model.allow_power_plot:
            self.toggle_power = tk.Button(
                controls, text="Hide Power",
                command=self._on_toggle_power_spectrum)
            buttons.append(self.toggle_power)

        if self.view_model.allow_power_settings:
            self.power_settings = tk.Button(
                controls, text="Power Settings",
                command=lambda: self._open_settings("power"))
            buttons.append(self.power_settings)

        if self.view_model.allow_band_settings:
            self.bands_settings = tk.Button(
                controls, text="Band Settings",
                command=lambda: self._open_settings("bands"))
            buttons.append(self.bands_settings)

        if self.view_model.allow_band_plot:
            hide_text, _ = self.view_model.get_band_button_labels()
            self.toggle_bands = tk.Button(
                controls, text=hide_text,
                command=self._on_toggle_band_power)
            buttons.append(self.toggle_bands)

        TOTAL_COLS = 12
        center_col = TOTAL_COLS // 2
        button_count = len(buttons)

        self.button_pause = tk.Button(
            controls, text="Play/Pause", command=self._on_play_pause)

        if button_count % 2 == 0:
            self.button_pause.grid(row=0, column=center_col - 1, columnspan=2, padx=6, pady=6)
        else:
            self.button_pause.grid(row=0, column=center_col, padx=6, pady=6)

        if button_count > 0:
            start_col = center_col - button_count // 2
            for i, button in enumerate(buttons):
                button.grid(row=1, column=start_col + i, padx=6, pady=6)

    def _refresh_channel_states(self):
        for entry in self.source_selectors:
            stream_name = entry["stream_var"].get()
            channel_cb = entry["channel_cb"]
            channel_var = entry["channel_var"]

            if stream_name == CHOOSE_STREAM:
                if channel_var.get() != CHOOSE_CHANNEL:
                    channel_var.set(CHOOSE_CHANNEL)
                    self._on_source_change()
                channel_cb.configure(state="disabled")
                continue

            stream_names = self.view_model.get_stream_names()
            if stream_name not in stream_names:
                if channel_var.get() != CHOOSE_CHANNEL:
                    channel_var.set(CHOOSE_CHANNEL)
                    self._on_source_change()
                channel_cb.configure(state="disabled")
                continue

            stream_idx = stream_names.index(stream_name)
            stream = self.view_model.streams[stream_idx]

            if not self.view_model.simulated and not stream.is_alive():
                if channel_var.get() != CHOOSE_CHANNEL:
                    channel_var.set(CHOOSE_CHANNEL)
                    self._on_source_change()
                channel_cb.configure(state="disabled")
                continue

            data = self.view_model._get_data_for_stream(stream_idx)
            if data is None or data.ndim != 2:
                if channel_var.get() != CHOOSE_CHANNEL:
                    channel_var.set(CHOOSE_CHANNEL)
                    self._on_source_change()
                channel_cb.configure(state="disabled")
                continue

            n_ch = data.shape[1]
            channel_cb["values"] = [CHOOSE_CHANNEL] + [str(i) for i in range(1, n_ch + 1)]
            channel_cb.configure(state="readonly")

            if channel_var.get() not in channel_cb["values"]:
                channel_var.set(CHOOSE_CHANNEL)

    def _start_channel_state_updater(self):
        self._refresh_channel_states()
        self.frame.after(200, self._start_channel_state_updater)

    def _update_channel_choices(self, stream_var, channel_var):
        stream_name = stream_var.get()

        for entry in self.source_selectors:
            if entry["stream_var"] is stream_var:
                channel_cb = entry["channel_cb"]

        if stream_name == CHOOSE_STREAM:
            if channel_var.get() != CHOOSE_CHANNEL:
                channel_var.set(CHOOSE_CHANNEL)
            channel_cb.configure(state="disabled")
            self._on_source_change()
            return

        stream_names = self.view_model.get_stream_names()
        stream_idx = stream_names.index(stream_name)
        stream = self.view_model.streams[stream_idx]

        if not self.view_model.simulated and not stream.is_alive():
            if channel_var.get() != CHOOSE_CHANNEL:
                channel_var.set(CHOOSE_CHANNEL)
            channel_cb.configure(state="disabled")
            self._on_source_change()
            return

        n_ch = stream.get_num_channels()
        channel_choices = [CHOOSE_CHANNEL] + [str(i) for i in range(1, n_ch + 1)]
        channel_cb.configure(state="readonly")
        channel_cb["values"] = channel_choices

        if channel_var.get() not in channel_choices:
            channel_var.set(CHOOSE_CHANNEL)

        self._on_source_change()

    def _on_source_change(self):
        sources = []
        stream_names = self.view_model.get_stream_names()

        for entry in self.source_selectors:
            stream_name = entry["stream_var"].get()
            ch_val = entry["channel_var"].get()

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

        self.view_model.set_selected_sources(sources)

        with self.plot_queue.mutex:
            self.plot_queue.queue.clear()

        self._y_limits = {
            "amplitude": [None, None],
            "power":     [None, None],
            "bands":     [None, None],
        }
        self._pending_ylimits = {}
        plot_data = self.view_model.get_plot_data()
        self._render_plot_data(plot_data)

    def _clear_graphs(self):
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
        self._process_plot_queue()

    def _plot_loop(self):
        while not self.stop_thread.is_set():
            if self.view_model.should_continue_plotting():
                try:
                    plot_data = self.view_model.get_plot_data()
                    try:
                        self.plot_queue.put(plot_data, block=False)
                    except queue.Full:
                        try:
                            self.plot_queue.get_nowait()
                            self.plot_queue.put(plot_data, block=False)
                        except BaseException:
                            pass
                except Exception as e:
                    print(f"Error in plot loop: {e}")
            time.sleep(0.05)

    def _process_plot_queue(self):
        try:
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
        self._update_band_toggle_state()
        if not plot_data.get("has_data", False):
            self._clear_graphs()
            return

        self.fig.clear()

        if not signals:
            self._show_no_data_message()
        else:
            self._render_plots(plot_data)

        self.fig.tight_layout()
        self._reapply_ylimits()
        self.canvas.draw()

    def stop(self):
        self.stop_thread.set()
        if self.plot_thread and self.plot_thread.is_alive():
            self.plot_thread.join(timeout=1.0)

    def on_notify(self, eventData, event) -> None:
        if event == EventType.STREAMLISTUPDATE:
            self._channel_cache.clear()
            for entry in self.source_selectors:
                values = [CHOOSE_STREAM] + eventData
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
        self._channel_cache.clear()
        is_playing = self.view_model.toggle_plotting()

        if is_playing:
            self._refresh_channel_states()
            self._on_source_change()
            with self.plot_queue.mutex:
                self.plot_queue.queue.clear()

        self._on_source_change()
        plot_data = self.view_model.get_plot_data()
        self._render_plot_data(plot_data)

        with self.plot_queue.mutex:
            self.plot_queue.queue.clear()

        for entry in self.source_selectors:
            values = [CHOOSE_STREAM] + self.view_model.get_stream_names()
            entry["stream_cb"]["values"] = values
            if entry["stream_var"].get() not in values:
                entry["stream_var"].set(CHOOSE_STREAM)
                entry["channel_var"].set(CHOOSE_CHANNEL)
                entry["channel_cb"]["values"] = [CHOOSE_CHANNEL]

        self._on_source_change()
        for entry in self.source_selectors:
            if entry["stream_var"].get() != CHOOSE_STREAM:
                self._update_channel_choices(entry["stream_var"], entry["channel_var"])

    def _on_toggle_amp(self):
        show_amplitude = self.view_model.toggle_amplitude()
        self.toggle_amplitude.config(text="Hide Amp" if show_amplitude else "Show Amp")

    def _on_toggle_power_spectrum(self):
        show_power = self.view_model.toggle_power_spectrum()
        self.toggle_power.config(text="Hide Power" if show_power else "Show Power")

    def _on_toggle_band_power(self):
        show_bands = self.view_model.toggle_band_power()
        hide_text, show_text = self.view_model.get_band_button_labels()
        self.toggle_bands.config(text=hide_text if show_bands else show_text)

    def _update_band_toggle_state(self):
        any_visible = self.view_model.any_band_visible()
        hide_text, show_text = self.view_model.get_band_button_labels()
        if not any_visible:
            self.toggle_bands.config(state=tk.DISABLED, text=show_text)
        else:
            self.toggle_bands.config(
                state=tk.NORMAL,
                text=hide_text if self.view_model.show_bands else show_text)

    def _open_settings(self, graph_type):
        popup = tk.Toplevel(self.frame)
        popup.title(f"{graph_type.capitalize()} Settings")
        popup.resizable(False, False)

        current_labels = self.view_model.labels[graph_type]
        manual = self._manual_limits[graph_type]

        tk.Label(popup, text="Graph Title:").grid(row=0, column=0, sticky="w", padx=8, pady=3)
        title_entry = tk.Entry(popup, width=22)
        title_entry.insert(0, current_labels["title"])
        title_entry.grid(row=0, column=1, padx=8, pady=3)

        tk.Label(popup, text="X-axis Label:").grid(row=1, column=0, sticky="w", padx=8, pady=3)
        xlabel_entry = tk.Entry(popup, width=22)
        xlabel_entry.insert(0, current_labels["xlabel"])
        xlabel_entry.grid(row=1, column=1, padx=8, pady=3)

        tk.Label(popup, text="Y-axis Label:").grid(row=2, column=0, sticky="w", padx=8, pady=3)
        ylabel_entry = tk.Entry(popup, width=22)
        ylabel_entry.insert(0, current_labels["ylabel"])
        ylabel_entry.grid(row=2, column=1, padx=8, pady=3)

        tk.Label(popup, text="Y-axis Range", font=("Arial", 10, "bold")).grid(
            row=3, column=0, columnspan=2, pady=(10, 2), sticky="w", padx=8)

        tk.Label(popup, text="Y Min (leave blank for auto):").grid(
            row=4, column=0, sticky="w", padx=8, pady=3)
        ymin_entry = tk.Entry(popup, width=22)
        if manual["y_min"] is not None:
            ymin_entry.insert(0, str(manual["y_min"]))
        ymin_entry.grid(row=4, column=1, padx=8, pady=3)

        tk.Label(popup, text="Y Max (leave blank for auto):").grid(
            row=5, column=0, sticky="w", padx=8, pady=3)
        ymax_entry = tk.Entry(popup, width=22)
        if manual["y_max"] is not None:
            ymax_entry.insert(0, str(manual["y_max"]))
        ymax_entry.grid(row=5, column=1, padx=8, pady=3)

        error_label = tk.Label(popup, text="", fg="red")
        error_label.grid(row=6, column=0, columnspan=2)

        row = 7

        band_vars = {}
        if graph_type == "bands":
            tk.Label(popup, text="Visible Bands:", font=("Arial", 10, "bold")).grid(
                row=row, column=0, columnspan=2, pady=(10, 4), sticky="w", padx=8)
            row += 1
            visibility = self.view_model.get_band_visibility()
            for band, is_visible in visibility.items():
                var = tk.BooleanVar(value=is_visible)
                band_vars[band] = var
                tk.Checkbutton(popup, text=band, variable=var).grid(
                    row=row, column=0, columnspan=2, sticky="w", padx=8)
                row += 1
            self._update_band_toggle_state()

        def apply_settings():
            raw_min = ymin_entry.get().strip()
            raw_max = ymax_entry.get().strip()
            y_min = None
            y_max = None

            try:
                if raw_min:
                    y_min = float(raw_min)
                if raw_max:
                    y_max = float(raw_max)
            except ValueError:
                error_label.config(text="Y Min/Max must be numbers or blank.")
                return

            if y_min is not None and y_max is not None and y_min >= y_max:
                error_label.config(text="Y Min must be less than Y Max.")
                return

            self._manual_limits[graph_type]["y_min"] = y_min
            self._manual_limits[graph_type]["y_max"] = y_max
            self._y_limits[graph_type] = [None, None]

            self.view_model.update_labels(
                graph_type, title_entry.get(), xlabel_entry.get(), ylabel_entry.get())

            if graph_type == "bands":
                for band, var in band_vars.items():
                    self.view_model.set_band_visibility(band, var.get())

            popup.destroy()

        tk.Button(popup, text="Apply", command=apply_settings).grid(
            row=row, column=0, columnspan=2, pady=10)

    def plot(self):
        pass

    def _show_no_data_message(self):
        ax = self.fig.add_subplot(111)
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        ax.set_axis_off()

    def _reapply_ylimits(self):
        """Re-apply y-limits after tight_layout() resets them."""
        for graph_type, (ax, lo, hi) in self._pending_ylimits.items():
            ax.set_ylim(lo, hi)

    def _apply_ylim(self, ax, graph_type, auto_lo, auto_hi):
        """
        Compute the final y-limits for an axis, combining auto-calculated
        bounds with any manual override from settings. Disables matplotlib
        autoscaling so the chosen limits are never overridden by bar/line data.
        """
        manual = self._manual_limits[graph_type]
        final_lo = manual["y_min"] if manual["y_min"] is not None else auto_lo
        final_hi = manual["y_max"] if manual["y_max"] is not None else auto_hi

        # Disable autoscaling so bars/lines cannot push the axis beyond our limits
        ax.set_ylim(final_lo, final_hi)
        # Lock it so tight_layout and data rendering don't override it
        ax.set_autoscaley_on(False)
        # Store for re-application after tight_layout
        self._pending_ylimits[graph_type] = (ax, final_lo, final_hi)

    def _render_plots(self, plot_data):
        self._pending_ylimits = {}
        if plot_data['n_subplots'] == 0:
            self._show_no_data_message()
            return

        signals = plot_data['signals']
        time_axes = plot_data['time_axes']
        subplot_index = 1

        # -------- AMPLITUDE --------
        if plot_data['show_amplitude']:
            ax = self.fig.add_subplot(plot_data['n_subplots'], 1, subplot_index)

            for sig, t, (stream_idx, ch_idx) in zip(signals, plot_data["time_axes"], plot_data["sources"]):
                stream_name = self.view_model.get_stream_names()[stream_idx]
                ax.plot(t, sig, label=f"{stream_name} · Ch {ch_idx + 1}")

            ax.set_title(plot_data['labels']['amplitude']['title'])
            ax.set_xlabel(plot_data['labels']['amplitude']['xlabel'])
            ax.set_ylabel(plot_data['labels']['amplitude']['ylabel'])
            ax.legend(loc="upper right", fontsize=8, frameon=True, framealpha=0.5,
                      handlelength=1.2, handletextpad=0.4, labelspacing=0.3, borderpad=0.3)

            subplot_index += 1

            # Smooth auto-scaling
            all_data = np.concatenate(signals) if signals else np.array([0])
            data_min, data_max = np.min(all_data), np.max(all_data)
            padding = 0.05 * (data_max - data_min + 1e-9)
            target_lo = data_min - padding
            target_hi = data_max + padding

            alpha = 0.2
            prev_lo, prev_hi = self._y_limits["amplitude"]
            if prev_lo is None:
                new_lo, new_hi = target_lo, target_hi
            else:
                new_lo = alpha * target_lo + (1 - alpha) * prev_lo
                new_hi = alpha * target_hi + (1 - alpha) * prev_hi
            self._y_limits["amplitude"] = [new_lo, new_hi]

            self._apply_ylim(ax, "amplitude", new_lo, new_hi)
            ax.margins(x=0)

            window = 2
            valid_times = [t for t in time_axes if len(t) > 0]
            if valid_times:
                t_max = max(t[-1] for t in valid_times)
                ax.set_xlim(max(0, t_max - window), t_max)

        # -------- POWER SPECTRUM --------
        if plot_data['show_power']:
            ax = self.fig.add_subplot(plot_data['n_subplots'], 1, subplot_index)

            for psd, freqs, (stream_idx, ch_idx) in zip(
                    plot_data["psds"], plot_data["freqs_list"], plot_data["sources"]):
                n = min(len(psd), len(freqs))
                ax.plot(freqs[:n], psd[:n],
                        label=f"{self.view_model.get_stream_names()[stream_idx]} · Ch {ch_idx + 1}")

            ax.set_title(plot_data['labels']['power']['title'])
            ax.set_xlabel(plot_data['labels']['power']['xlabel'])
            ax.set_ylabel(plot_data['labels']['power']['ylabel'])

            subplot_index += 1

            all_psd = np.concatenate(plot_data["psds"]) if plot_data["psds"] else np.array([0])
            data_min, data_max = np.min(all_psd), np.max(all_psd)

            prev_lo, prev_hi = self._y_limits["power"]
            if prev_lo is None:
                new_lo, new_hi = data_min, data_max
            else:
                new_lo = min(prev_lo, data_min)
                new_hi = max(prev_hi, data_max)
            if new_hi - new_lo < 1e-6:
                new_hi += 1e-3
                new_lo -= 1e-3
            self._y_limits["power"] = [new_lo, new_hi]

            self._apply_ylim(ax, "power", new_lo, new_hi)

            # x-axis: show full frequency range (0 to Nyquist)
            all_freqs = np.concatenate(plot_data["freqs_list"]) if plot_data["freqs_list"] else np.array([0, 125])
            ax.set_xlim(0, np.max(all_freqs))

        # -------- BAND POWERS --------
        if plot_data['show_bands']:
            ax = self.fig.add_subplot(plot_data['n_subplots'], 1, subplot_index)

            band_labels = plot_data['band_labels']
            band_powers = np.array(plot_data['band_powers'])
            n_channels, n_bands = band_powers.shape

            x = np.arange(n_bands)
            total_width = 0.8
            bar_width = total_width / n_channels

            for i, (stream_idx, ch_idx) in enumerate(plot_data["sources"]):
                stream_name = self.view_model.get_stream_names()[stream_idx]
                # bottom=0 is explicit — bars run from 0 upward in data space
                ax.bar(x + i * bar_width, band_powers[i],
                       width=bar_width, bottom=0,
                       label=f"{stream_name} · Ch {ch_idx + 1}")

            ax.set_xticks(x + total_width / 2 - bar_width / 2)
            ax.set_xticklabels(band_labels)
            ax.set_title(plot_data['labels']['bands']['title'])
            ax.set_xlabel(plot_data['labels']['bands']['xlabel'])
            ax.set_ylabel(plot_data['labels']['bands']['ylabel'])

            all_bands = band_powers.flatten()
            data_min, data_max = np.min(all_bands), np.max(all_bands)

            prev_lo, prev_hi = self._y_limits["bands"]
            if prev_lo is None:
                new_lo, new_hi = data_min, data_max
            else:
                new_lo = min(prev_lo, data_min)
                new_hi = max(prev_hi, data_max)
            if new_hi - new_lo < 1e-6:
                new_hi += 1e-3
                new_lo -= 1e-3
            self._y_limits["bands"] = [new_lo, new_hi]

            self._apply_ylim(ax, "bands", new_lo, new_hi)


# Factory function
def create_plotter(frame: tk.Frame, user_model, session_id: int = 0):
    view_model = PlotterViewModel(user_model, session_id=session_id)
    view = PlotterView(frame, view_model)
    return view_model, view

