import tkinter as tk
from eventClass import *
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)
from matplotlib.figure import Figure
from plotterViewModel import PlotterViewModel


class PlotterView(EventClass):
    def __init__(self, frame: tk.Frame, view_model: PlotterViewModel):
        super().__init__()
        self.frame = frame
        self.view_model = view_model
        

        self.subscribe_to_subject(self.view_model)
        
        
        self.fig = Figure(figsize=(6, 8), dpi=100)  # taller for multiple plots
        
        self._setup_canvas()
        self._setup_controls()
        
        
        self.plot()

    def _setup_canvas(self):
        
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame)
        self.canvas.draw()
        self.canvas.mpl_connect("key_press_event",
                                lambda event: print(f"you pressed {event.key}"))
        self.canvas.mpl_connect("key_press_event", key_press_handler)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def _setup_controls(self):
        
        controls = tk.Frame(self.frame, bd=1, relief=tk.FLAT)
        controls.pack(side=tk.BOTTOM, fill=tk.X, before=self.canvas.get_tk_widget())

        for col in range(6):
            controls.grid_columnconfigure(col, weight=1, uniform="controls")

        self.button_pause = tk.Button(controls, text="Play/Pause", command=self._on_play_pause)
        self.button_pause.grid(row=0, column=0, columnspan=6, padx=6, pady=6, sticky="n")

        
        try:
            current_stream = self.view_model.get_current_stream_name()
        except Exception:
            
            current_stream = (self.view_model.get_stream_names()[0] if hasattr(self.view_model, "get_stream_names") and self.view_model.get_stream_names() else
                              (self.view_model.stream_names[0] if hasattr(self.view_model, "stream_names") and self.view_model.stream_names else ""))

        try:
            stream_names = self.view_model.get_stream_names()
        except Exception:
            stream_names = getattr(self.view_model, "stream_names", []) or []

        if not stream_names:
            stream_names = ["No Streams"]
        

        self.selected_stream = tk.StringVar(value=current_stream if current_stream else stream_names[0])
        
        self.stream_menu = tk.OptionMenu(controls, self.selected_stream, *stream_names, command=self._on_change_stream)
        self.stream_menu.grid(row=0, column=0, padx=6, pady=6, sticky="w")

        

        self.toggle_amplitude = tk.Button(controls, text="Hide Amp", command=self._on_toggle_amp)
        self.toggle_amplitude.grid(row=1, column=0, padx=6, pady=6, sticky="ew")

        self.amp_settings = tk.Button(controls, text="Amp Settings", command=lambda: self._open_settings("amplitude"))
        self.amp_settings.grid(row=1, column=1, padx=6, pady=6, sticky="ew")

        

        self.toggle_power = tk.Button(controls, text="Hide Power", command=self._on_toggle_power_spectrum)
        self.toggle_power.grid(row=1, column=2, padx=6, pady=6, sticky="ew")

        self.power_settings = tk.Button(controls, text="Power Settings", width = 15, command=lambda: self._open_settings("power"))
        self.power_settings.grid(row=1, column=3, padx=6, pady=6, sticky="ew")

        self.toggle_bands = tk.Button(controls, text="Hide Band", command=self._on_toggle_band_power)
        self.toggle_bands.grid(row=1, column=4, padx=6, pady=6, sticky="ew")

        self.bands_settings = tk.Button(controls, text="Band Settings", command=lambda: self._open_settings("bands"))
        self.bands_settings.grid(row=1, column=5, padx=6, pady=6, sticky="ew")

        

    def on_notify(self, eventData, event) -> None:
        if event == EventType.STREAMLISTUPDATE:
            self._refresh_stream_menu(eventData)

    def _refresh_stream_menu(self, stream_names):
        self.selected_stream.set('')
        self.stream_menu['menu'].delete(0, 'end')

        for stream in stream_names:
            self.stream_menu['menu'].add_command(
                label=stream, 
                command=tk._setit(self.selected_stream, stream, self._on_change_stream)
            )
        
        if stream_names:
            self.selected_stream.set(stream_names[0])

    def _on_play_pause(self):
        should_start = self.view_model.toggle_plotting()
        if should_start:
            self.plot()

    def _on_change_stream(self, selection):
        success = self.view_model.change_stream(selection)
        if success:
            self.plot()  # force redraw

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
        popup = tk.Toplevel(self.frame)
        popup.title(f"{graph_type.capitalize()} Settings")

        
        plot_data = self.view_model.get_plot_data()
        current_labels = plot_data['labels'][graph_type]

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

        def apply_settings():
            
            success = self.view_model.update_labels(
                graph_type, 
                title_entry.get(), 
                xlabel_entry.get(), 
                ylabel_entry.get()
            )
            if success:
                popup.destroy()

        tk.Button(popup, text="Apply", command=apply_settings).grid(row=3, column=0, columnspan=2)

    def plot(self):
        # Get all plotting data from ViewModel
        plot_data = self.view_model.get_plot_data()
        
        self.fig.clear()  # clear figure before redrawing

        if not plot_data['has_data']:
            self._show_no_data_message()
        else:
            self._render_plots(plot_data)

        # refresh canvas
        self.fig.tight_layout()
        self.canvas.draw()
        self.canvas.flush_events()

        if self.view_model.should_continue_plotting():
            self.frame.after(10, self.plot)

    def _show_no_data_message(self):
        ax = self.fig.add_subplot(111)
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        ax.set_axis_off()

    def _render_plots(self, plot_data):
        subplot_index = 1
        labels = plot_data['labels']
        
        if plot_data['show_amplitude']:
            ax1 = self.fig.add_subplot(plot_data['n_subplots'], 1, subplot_index)
            subplot_index += 1
            ax1.plot(plot_data['time_axis'], plot_data['data'], color="blue")
            
            ax1.set_title(labels["amplitude"]["title"])
            ax1.set_ylabel(labels["amplitude"]["ylabel"])
            ax1.set_xlabel(labels["amplitude"]["xlabel"])
            ax1.set_ylim([-100, 100])

        if plot_data['show_power']:
            ax2 = self.fig.add_subplot(plot_data['n_subplots'], 1, subplot_index)
            subplot_index += 1
            ax2.plot(plot_data['freqs'], plot_data['psd'], color="green")
            ax2.set_xlim([0, 50])  # up to 50 Hz
            ax2.set_title(labels["power"]["title"])
            ax2.set_xlabel(labels["power"]["xlabel"])
            ax2.set_ylabel(labels["power"]["ylabel"])

        if plot_data['show_bands']:
            ax3 = self.fig.add_subplot(plot_data['n_subplots'], 1, subplot_index)
            ax3.bar(plot_data['band_labels'], plot_data['band_powers'], color="orange")
            ax3.set_title(labels["bands"]["title"])
            ax3.set_xlabel(labels["bands"]["xlabel"])
            ax3.set_ylabel(labels["bands"]["ylabel"])
            ax3.tick_params(axis='x', rotation=30)

# Changed: Factory function to create both ViewModel and View together
def create_plotter(frame: tk.Frame, user_model):
    """Factory function to create a complete plotter with ViewModel and View"""
    view_model = PlotterViewModel(user_model)
    view = PlotterView(frame, view_model)
    return view_model, view