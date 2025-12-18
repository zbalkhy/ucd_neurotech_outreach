import tkinter as tk
from tkinter import ttk
from eventClass import *
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)
from matplotlib.figure import Figure
from plotterViewModel import PlotterViewModel
import threading
import queue
import time


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
            current_stream = ""

        try:
            stream_names = self.view_model.get_stream_names()
        except Exception:
            stream_names = []

        if not stream_names:
            stream_names = ["No Streams"]

        self.selected_stream = tk.StringVar(value=current_stream if current_stream else stream_names[0])
        
        self.stream_menu = ttk.Combobox(
            controls,
            textvariable=self.selected_stream,
            values=stream_names,
            state="readonly",
            width=20
        )
        self.stream_menu.bind("<<ComboboxSelected>>",
                            lambda e: self._on_change_stream(self.selected_stream.get()))
        
        # Control-click on combobox opens context menu to rename/delete selected item
        # This is for Mac only. Right-click for Windows please
        self.stream_menu.bind("<Button-3>", self._on_stream_context_menu)  # Windows right-click
        self.stream_menu.bind("<Button-2>", self._on_stream_context_menu)  # Mac right-click
        self.stream_menu.bind("<Control-Button-1>", self._on_stream_context_menu)  # mac Ctrl-click

        # Hover enter/leave for tooltip showing inherent stream name
        self.stream_menu.bind("<Enter>", self._on_stream_hover_enter)
        self.stream_menu.bind("<Leave>", self._on_stream_hover_leave)
        
        self.stream_menu.grid(row=0, column=0, padx=6, pady=6, sticky="ew")

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
    
    # ------------------------------
    # Right-click context + rename
    # ------------------------------
    def _on_stream_context_menu(self, event):
        """Show a context menu that stays open until Close Menu is clicked."""
        current = self.selected_stream.get()
        if not current or current == "No Streams":
            return

        # Close any existing menu
        self._close_context_menu()

        menu = tk.Toplevel(self.frame)
        menu.wm_overrideredirect(True)
        menu.lift()
        menu.attributes("-topmost", True)
        menu.geometry(f"+{event.x_root+25}+{event.y_root}")

        # Keep it open even if focus changes
        menu.grab_set_global()  # keeps events directed here until closed

        # Build simple buttons for menu actions
        btn_rename = tk.Button(menu, text="Rename",
                            command=lambda: self._open_rename_and_close(menu, current))
        btn_rename.pack(fill="x", padx=4, pady=2)

        btn_delete = tk.Button(menu, text="Delete", fg="red",
                            command=lambda: self._on_delete_stream_and_close(menu, current))
        btn_delete.pack(fill="x", padx=4, pady=2)

        btn_close = tk.Button(menu, text="Close Menu", bg="#ddd",
                            command=self._close_context_menu)
        btn_close.pack(fill="x", padx=4, pady=2)

        # Save reference
        self._context_menu = menu

    def _open_rename_and_close(self, menu, current_display):
        self._close_context_menu()
        self._open_rename_popup(current_display)

    def _on_delete_stream_and_close(self, menu, stream_name):
        """Delete the selected stream safely and clear the plot if needed."""
        self._close_context_menu()

        confirm = tk.Toplevel(self.frame)
        confirm.title("Confirm Delete")
        confirm.transient(self.frame)
        confirm.geometry("+400+250")

        tk.Label(confirm, text=f"Delete stream '{stream_name}'?", padx=10, pady=10).pack()

        btn_frame = tk.Frame(confirm)
        btn_frame.pack(pady=5)

        def do_delete():
            success = self.view_model.delete_stream_by_name(stream_name)
            confirm.destroy()
            if success:
                # Refresh dropdown list
                updated = self.view_model.get_stream_names()
                self._refresh_stream_menu(updated)

                
                if self.selected_stream.get() == stream_name:
                    if updated:
                        # Select first remaining stream
                        self.selected_stream.set(updated[0])
                        self._on_change_stream(updated[0])
                    else:
                        # No streams left — clear graphs and show "No data"
                        self.selected_stream.set("No Streams")
                        self._clear_graphs()
                else:
                    self._on_change_stream(self.selected_stream.get())
            else:
                print(f"[PlotterView] delete failed for '{stream_name}'")

        tk.Button(btn_frame, text="Delete", fg="red", command=do_delete).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancel", command=confirm.destroy).pack(side="left", padx=5)

    def _close_context_menu(self):
        if getattr(self, "_context_menu", None):
            try:
                self._context_menu.grab_release()
                self._context_menu.destroy()
            except Exception:
                pass
            self._context_menu = None

    def _open_rename_popup(self, old_name):
        """Open rename popup for old_name (display name)."""
        popup = tk.Toplevel(self.frame)
        popup.title(f"Rename Stream: {old_name}")
        popup.transient(self.frame)

        tk.Label(popup, text="Old Name:").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        tk.Label(popup, text=old_name).grid(row=0, column=1, padx=6, pady=6, sticky="w")

        tk.Label(popup, text="New Name:").grid(row=1, column=0, padx=6, pady=6, sticky="w")
        new_name_entry = tk.Entry(popup)
        new_name_entry.grid(row=1, column=1, padx=6, pady=6, sticky="ew")
        new_name_entry.insert(0, old_name)
        new_name_entry.focus_set()

        def apply_new_name():
            new_name = new_name_entry.get().strip()
            if not new_name:
                return
            success = self.view_model.rename_stream(old_name, new_name)
            if success:
                # update combobox values while preserving selection if possible
                updated = self.view_model.get_stream_names()
                self._refresh_stream_menu(updated, new_selection=new_name)
                popup.grab_release()
                popup.destroy()
            else:
                popup.grab_release()
                popup.destroy()

        tk.Button(popup, text="Apply", command=apply_new_name).grid(row=2, column=0, columnspan=2, pady=8)
        popup.columnconfigure(1, weight=1)

    
    def _clear_graphs(self):
        """Clear all graph axes and display 'No data'."""
        try:
            self.fig.clear()
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, "No data", ha="center", va="center")
            ax.set_axis_off()
            self.canvas.draw()
            
        except Exception as e:
            print("[PlotterView] Error clearing graphs:", e)
    
    # Hover tooltip for inherent name
    def _on_stream_hover_enter(self, event):
        """Show a small tooltip with the inherent stream name for the current selection."""
        display = self.selected_stream.get()
        if not display:
            return
        inherent = self.view_model.get_inherent_name(display)
        if not inherent:
            return

        # Create tooltip window if it doesn't exist
        if getattr(self, "_stream_tooltip", None) is None:
            self._stream_tooltip = tk.Toplevel(self.frame)
            self._stream_tooltip.wm_overrideredirect(True)  # no window decorations
            lbl = tk.Label(self._stream_tooltip, text=f"Inherent: {inherent}", bd=1, relief='solid', padx=4, pady=2)
            lbl.pack()
        # position tooltip near mouse
        x = event.x_root + 10
        y = event.y_root + 10
        self._stream_tooltip.wm_geometry(f"+{x}+{y}")

    def _on_stream_hover_leave(self, event):
        if getattr(self, "_stream_tooltip", None):
            try:
                self._stream_tooltip.destroy()
            except Exception:
                pass
            self._stream_tooltip = None

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
        """Render the plot data in the UI thread - Added: Separated from plot loop"""
        self.fig.clear()

        if not plot_data['has_data']:
            self._show_no_data_message()
        else:
            self._render_plots(plot_data)
        
        # refresh canvas
        self.fig.tight_layout()
        self.canvas.draw()
        self.canvas.flush_events()
    
    def stop(self):
        """Stop the plotting thread - Added: Cleanup method"""
        self.stop_thread.set()
        if self.plot_thread and self.plot_thread.is_alive():
            self.plot_thread.join(timeout=1.0)

    def on_notify(self, eventData, event) -> None:
        if event == EventType.STREAMLISTUPDATE:
            if eventData and len(eventData) > 0:
                self.stream_menu["values"] = eventData
                current = self.selected_stream.get()
                if current in eventData:
                    self.selected_stream.set(current)
                else:
                    self.selected_stream.set(eventData[0])
            else:
                # No streams left — set dropdown to "No Streams"
                self.stream_menu["values"] = ["No Streams"]
                self.selected_stream.set("No Streams")

        elif event == EventType.CLEARALLPLOTS:
            self.stream_menu["values"] = ["No Streams"]
            self.selected_stream.set("No Streams")
            self._clear_graphs()

    def _refresh_stream_menu(self, stream_names, new_selection=None):
        # preserve current selection if possible
        current = self.selected_stream.get()
        self.stream_menu["values"] = stream_names
        if new_selection and new_selection in stream_names:
            self.selected_stream.set(new_selection)
        elif current in stream_names:
            self.selected_stream.set(current)
        elif stream_names:
            self.selected_stream.set(stream_names[0])

    def _on_play_pause(self):
        """Handle play/pause button click - Fixed: Don't call plot() - thread handles it"""
        should_start = self.view_model.toggle_plotting()
        # Thread automatically responds to state change - no manual plot() needed

    def _on_change_stream(self, selection):
        """Handle stream selection change - Fixed: Don't call plot() - thread handles it"""
        success = self.view_model.change_stream(selection)
        # Thread will automatically get new stream data on next iteration

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