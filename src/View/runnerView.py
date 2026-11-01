"""Tk setup and gameplay surfaces for the EEG runner."""

import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk

from Classes.eventClass import EventClass
from Stream.gameControlStream import channel_count


class RunnerView(EventClass):
    def __init__(self, root, view_model):
        super().__init__()
        self.root = root
        self.view_model = view_model
        self.closed = False
        self._callbacks = {}
        self._bindings = []
        self._threshold_initialized = False
        self.subscribe_to_subject(view_model)
        root.title("EEG Runner")
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._bind("<KeyPress-space>", self.on_space_press)
        self._bind("<KeyRelease-space>", self.on_space_release)
        self._bind("<KeyPress-r>", self.on_restart_key)
        self._bind("<KeyPress-R>", self.on_restart_key)
        self._bind("<FocusOut>", self.on_focus_out)
        self._bind("<Destroy>", self.on_destroy)
        self.show_setup()

    def _bind(self, sequence, callback):
        binding = self.root.bind(sequence, callback, add="+")
        self._bindings.append((sequence, binding))

    def _schedule(self, key, delay, callback):
        def invoke():
            self._callbacks.pop(key, None)
            if not self.closed:
                callback()
        self._callbacks[key] = self.root.after(delay, invoke)

    def _clear_screen(self):
        for callback in self._callbacks.values():
            self.root.after_cancel(callback)
        self._callbacks.clear()
        for child in self.root.winfo_children():
            child.destroy()

    def show_setup(self):
        self._clear_screen()
        self.view_model.stop_run()
        self.root.geometry("620x470")
        self.root.minsize(560, 440)
        self.body = ttk.Frame(self.root, padding=24)
        self.body.pack(fill="both", expand=True)
        ttk.Label(self.body, text="Choose your controller",
                  font=("Arial", 20, "bold")).pack(anchor="w", pady=(0, 16))
        self.mode = tk.StringVar(value=self.view_model.mode)
        choices = ttk.Frame(self.body)
        choices.pack(fill="x", pady=(0, 16))
        for label, value in (("Keyboard", "keyboard"),
                             ("Control stream", "label"),
                             ("Alpha threshold", "alpha")):
            ttk.Radiobutton(choices, text=label, value=value,
                            variable=self.mode, command=self._change_mode).pack(
                                side="left", padx=(0, 16))
        self.options = ttk.Frame(self.body)
        self.options.pack(fill="x")
        self.setup_message = tk.StringVar()
        ttk.Label(self.body, textvariable=self.setup_message,
                  wraplength=550).pack(anchor="w", pady=16)
        self.start_button = ttk.Button(self.body, text="Start run",
                                       command=self.start_run)
        self.start_button.pack(anchor="e", side="bottom")
        self._build_options()
        self._poll_setup()

    def _change_mode(self):
        self.view_model.select_mode(self.mode.get())
        self._build_options()
        self._refresh_setup()

    def _build_options(self):
        for child in self.options.winfo_children():
            child.destroy()
        vm = self.view_model
        self._sources = []
        if vm.mode == "keyboard":
            ttk.Label(self.options, text="Hold Space for the upper lane.\n"
                      "Release Space for the lower lane.\n\n"
                      "Press R or use Restart to begin a fresh run.").pack(
                          anchor="w")
            return
        ttk.Label(self.options, text="Input stream").pack(anchor="w")
        self.source_combo = ttk.Combobox(self.options, state="readonly")
        self.source_combo.pack(fill="x", pady=(4, 12))
        self.source_combo.bind("<<ComboboxSelected>>", self._change_source)
        if vm.mode == "label":
            ttk.Label(self.options, text="Upper-lane label").pack(anchor="w")
            self.active_label = tk.StringVar(value=vm.active_label)
            ttk.Entry(self.options, textvariable=self.active_label).pack(
                fill="x", pady=4)
            self.label_preview = tk.StringVar()
            ttk.Label(self.options, textvariable=self.label_preview,
                      wraplength=540).pack(anchor="w", pady=8)
            ttk.Label(self.options, text="Other labels select the lower lane.").pack(
                anchor="w")
        else:
            ttk.Label(self.options, text="Channel").pack(anchor="w")
            self.channel_combo = ttk.Combobox(self.options, state="readonly")
            self.channel_combo.pack(fill="x", pady=4)
            self.channel_combo.bind("<<ComboboxSelected>>", self._change_channel)
            self.invert = tk.BooleanVar(value=vm.invert)
            ttk.Checkbutton(self.options, text="Invert direction (at or below → upper lane)",
                            variable=self.invert).pack(anchor="w", pady=8)
            ttk.Label(self.options, text="Above threshold → upper lane by default.\n"
                      "The first alpha reading sets your starting threshold.\n"
                      "Adjust it beside the live power readout during play.",
                      wraplength=540).pack(anchor="w")

    def _change_source(self, event=None):
        index = self.source_combo.current()
        if 0 <= index < len(self._sources):
            self.view_model.select_source(self._sources[index])
        self._refresh_setup()

    def _change_channel(self, event=None):
        self.view_model.channel_index = self.channel_combo.current()
        self._refresh_setup()

    def _refresh_setup(self):
        vm = self.view_model
        if vm.mode != "keyboard":
            self._sources = vm.available_sources()
            self.source_combo.configure(
                values=[source.stream_name for source in self._sources])
            if vm.source in self._sources:
                self.source_combo.current(self._sources.index(vm.source))
            else:
                vm.source = None
                self.source_combo.set("")
            if vm.mode == "label":
                self.label_preview.set("Latest label: " + vm.preview_label())
            else:
                try:
                    count = channel_count(vm.source) if vm.source else 0
                except (ValueError, TypeError):
                    count = 0
                self.channel_combo.configure(
                    values=[f"Channel {i + 1}" for i in range(count)])
                if 0 <= vm.channel_index < count:
                    self.channel_combo.current(vm.channel_index)
                else:
                    self.channel_combo.set("")
        issue = vm.setup_status()
        self.setup_message.set(issue or "Ready to start")
        self.start_button.configure(state="disabled" if issue else "normal")

    def _poll_setup(self):
        self._refresh_setup()
        self._schedule("status", 100, self._poll_setup)

    def start_run(self):
        vm = self.view_model
        if vm.mode == "label":
            vm.active_label = self.active_label.get()
        elif vm.mode == "alpha":
            vm.invert = self.invert.get()
        try:
            vm.start_run()
        except Exception as error:
            self.setup_message.set(str(error))
            return
        self._clear_screen()
        self.root.geometry("850x850")
        self.root.minsize(650, 600)
        self.body = ttk.Frame(self.root, padding=12)
        self.body.pack(fill="both", expand=True)
        toolbar = ttk.Frame(self.body)
        toolbar.pack(fill="x", pady=(0, 8))
        ttk.Label(toolbar, text="EEG Runner", font=("Arial", 18, "bold")).pack(
            side="left")
        ttk.Button(toolbar, text="Change controller",
                   command=self.show_setup).pack(side="right", padx=(8, 0))
        ttk.Button(toolbar, text="Restart", command=vm.restart).pack(side="right")
        self.image_label = ttk.Label(self.body, anchor="center")
        self.image_label.pack(fill="both", expand=True)
        self.input_status = tk.StringVar()
        ttk.Label(self.body, textvariable=self.input_status,
                  wraplength=800).pack(anchor="w", pady=8)
        if vm.mode == "alpha":
            panel = ttk.LabelFrame(self.body, text="Alpha threshold", padding=10)
            panel.pack(fill="x")
            direction = "at or below" if vm.invert else "above"
            ttk.Label(panel, text=f"{vm.source.stream_name} · Channel {vm.channel_index + 1}"
                      f" · {direction} threshold → upper lane").pack(anchor="w")
            self.power_text = tk.StringVar(value="Alpha power (relative units): waiting")
            ttk.Label(panel, textvariable=self.power_text).pack(anchor="w", pady=4)
            row = ttk.Frame(panel)
            row.pack(fill="x")
            ttk.Label(row, text="Threshold").pack(side="left", padx=(0, 8))
            self.threshold_text = tk.StringVar()
            self.threshold_entry = ttk.Entry(row, textvariable=self.threshold_text,
                                             width=20, state="disabled")
            self.threshold_entry.pack(side="left")
            self.threshold_entry.bind("<Return>", self.apply_threshold)
            self.threshold_entry.bind("<FocusOut>", self.apply_threshold)
            ttk.Label(row, text="Enter or leave field to apply").pack(
                side="left", padx=8)
            self.threshold_error = tk.StringVar()
            ttk.Label(panel, textvariable=self.threshold_error,
                      foreground="#b42318").pack(anchor="w")
            self._threshold_initialized = False
        else:
            text = ("Hold SPACE for upper lane · R to restart" if vm.mode == "keyboard"
                    else f"{vm.source.stream_name} · Upper-lane label: {vm.active_label} · R to restart")
            ttk.Label(self.body, text=text, wraplength=800).pack(anchor="w")
        self.root.focus_set()
        self._render_frame()
        self._poll_game()

    def apply_threshold(self, event=None):
        controller = self.view_model.controller
        if controller is None or not self._threshold_initialized:
            return
        try:
            controller.set_threshold(self.threshold_text.get())
        except ValueError as error:
            self.threshold_error.set(str(error) + "; previous value retained.")
        else:
            self.threshold_error.set("")
        return "break"

    def _poll_game(self):
        vm = self.view_model
        state = vm.controller.read_state()
        prefix = "" if state.ready else "Paused — "
        message = prefix + state.message
        if state.label is not None:
            message += f" · Latest label: {state.label}"
        self.input_status.set("Game error: " + vm.game.error if vm.game.error else message)
        if vm.mode == "alpha":
            power = "waiting" if state.power is None else f"{state.power:.6g}"
            self.power_text.set("Alpha power (relative units): " + power)
            if state.threshold is not None and not self._threshold_initialized:
                self.threshold_text.set(repr(state.threshold))
                self.threshold_entry.configure(state="normal")
                self._threshold_initialized = True
        self._schedule("status", 100, self._poll_game)

    def _render_frame(self):
        game = self.view_model.game
        frame = game.read_frame()
        if frame is not None:
            image = Image.frombytes("RGB", (game.width, game.height), frame)
            width = max(1, self.image_label.winfo_width())
            height = max(1, self.image_label.winfo_height())
            image.thumbnail((width, height))
            photo = ImageTk.PhotoImage(image)
            self.image_label.configure(image=photo)
            self.image_label.image = photo
        self._schedule("frame", 16, self._render_frame)

    def _editing_text(self, event):
        return event.widget.winfo_class() in (
            "Entry", "TEntry", "Text", "Spinbox", "TSpinbox", "TCombobox")

    def on_space_press(self, event):
        if not self._editing_text(event):
            self.view_model.set_keyboard(True)

    def on_space_release(self, event):
        self.view_model.set_keyboard(False)

    def on_restart_key(self, event):
        if not self._editing_text(event):
            self.view_model.restart()

    def on_focus_out(self, event):
        self.view_model.set_keyboard(False)

    def on_notify(self, eventData, event):
        if not self.closed and self.view_model.game is None:
            self._refresh_setup()

    def on_destroy(self, event):
        if event.widget is self.root:
            self.on_close(destroy=False)

    def on_close(self, destroy=True):
        if self.closed:
            return
        self.closed = True
        for callback in self._callbacks.values():
            self.root.after_cancel(callback)
        self._callbacks.clear()
        for sequence, binding in self._bindings:
            self.root.unbind(sequence, binding)
        self._bindings.clear()
        self.dispose()
        self.view_model.dispose()
        if destroy:
            self.root.destroy()
