import tkinter as tk
from tkinter import ttk
from typing import Callable
from common import (
    MODAL_FIRST_ENTRY_LABEL,
    MODAL_SECOND_ENTRY_LABEL,
    MODAL_SEARCHING_FOR_DEVICE_LABEL,
    MODAL_FOUND_DEVICE_LABEL,
    MODAL_WIDGET_TITLE,
)


class TextEntryModalView:
    """A reusable modal dialog with text entries and submit/cancel actions."""

    def __init__(
            self,
            parent: tk.Misc,
            title: str = "Input",
            on_submit: Callable[[str, str], None] | None = None):
        self.parent = parent.winfo_toplevel()
        self.on_submit = on_submit
        self.parent_bounds = self._get_parent_bounds()

        self.window = tk.Toplevel(self.parent)
        self.window.attributes('-alpha', 0.5)
        self.window.withdraw()
        self.window.title(title)
        self.window.resizable(False, False)
        self.window.transient(self.parent)
        self.window.overrideredirect(True)

        # Closing the window should behave the same as pressing Cancel.
        self.window.protocol("WM_DELETE_WINDOW", self.cancel)
        self.window.bind("<Escape>", self.cancel)
        self.window.bind("<Return>", self.submit)

        self.entry_value = tk.StringVar()
        self.second_entry_value = tk.StringVar()
        self._build_widgets()
        self._center_over_parent()
        self.window.deiconify() # bring back to top level after centering
        self._make_modal()

    def _get_parent_bounds(self) -> tuple[int, int, int, int]:
        """Return fresh screen bounds for the parent to avoid mapping races."""
        self.parent.update_idletasks()

        width = self.parent.winfo_width()
        height = self.parent.winfo_height()
        if width <= 1:
            width = self.parent.winfo_reqwidth()
        if height <= 1:
            height = self.parent.winfo_reqheight()

        return (
            self.parent.winfo_rootx(),
            self.parent.winfo_rooty(),
            max(width, 1),
            max(height, 1),
        )

    def _build_widgets(self) -> None:
        """Build the modal content."""
        
        border_frame = tk.Frame(
            self.window,
            background="#d0d0d0",
            borderwidth=1,
            relief="solid")
        border_frame.grid(row=0, column=0, sticky="nsew")

        outer_frame = ttk.Frame(border_frame, padding=12)
        outer_frame.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        
        outer_frame_row = 0
        title_label = ttk.Label(
            outer_frame,
            text=MODAL_WIDGET_TITLE,
            font=("", 13, "bold"))
        title_label.grid(
            row=outer_frame_row,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 12))
        outer_frame_row += 1

        looking_for_device_label = ttk.Label(
            outer_frame,
            text=MODAL_SEARCHING_FOR_DEVICE_LABEL,
            font=("", 12, "bold"))
        looking_for_device_label.grid(row=outer_frame_row, column=0, columnspan=2, sticky="w")
        outer_frame_row += 1

        first_entry_label = ttk.Label(
            outer_frame,
            text=MODAL_FIRST_ENTRY_LABEL)
        first_entry_label.grid(row=outer_frame_row, column=0, columnspan=2, sticky="w")
        outer_frame_row += 1
        
        self.entry = ttk.Entry(
            outer_frame,
            textvariable=self.entry_value,
            width=36)
        self.entry.grid(row=outer_frame_row, column=0, columnspan=2,
                        sticky="ew", pady=(8, 12))
        outer_frame_row += 1

        second_entry_label = ttk.Label(
            outer_frame,
            text=MODAL_SECOND_ENTRY_LABEL)
        second_entry_label.grid(row=outer_frame_row, column=0, columnspan=2, sticky="w")
        outer_frame_row += 1
        
        self.second_entry = ttk.Entry(
            outer_frame,
            textvariable=self.second_entry_value,
            width=36)
        self.second_entry.grid(row=outer_frame_row, column=0, columnspan=2,
                               sticky="ew", pady=(8, 12))
        outer_frame_row += 1

        enter_button = ttk.Button(
            outer_frame,
            text="Enter",
            command=self.submit)
        enter_button.grid(row=outer_frame_row, column=0, sticky="e", padx=(0, 6))

        cancel_button = ttk.Button(
            outer_frame,
            text="Cancel",
            command=self.cancel)
        cancel_button.grid(row=outer_frame_row, column=1, sticky="w")

        outer_frame.columnconfigure(0, weight=1)
        outer_frame.columnconfigure(1, weight=1)

    def _center_over_parent(self) -> None:
        """Place the dialog near the center of the parent window."""
        self.parent_bounds = self._get_parent_bounds()
        self.window.update_idletasks()
        parent_x, parent_y, parent_width, parent_height = self.parent_bounds
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()
        if window_width <= 1:
            window_width = self.window.winfo_reqwidth()
        if window_height <= 1:
            window_height = self.window.winfo_reqheight()

        x_position = parent_x + max((parent_width - window_width) // 2, 0)
        y_position = parent_y + max((parent_height - window_height) // 2, 0)
        self.window.geometry(
            f"{window_width}x{window_height}+{x_position}+{y_position}")

    def _make_modal(self) -> None:
        """Force interaction to stay inside this dialog until it closes."""
        self.window.wait_visibility()
        self.window.lift(self.parent)
        self.window.grab_set()

        # Recenter after mapping. This handles override-redirect timing on X11.
        self._center_over_parent()

        self.entry.focus_force()

    def submit(self, event: tk.Event | None = None) -> None:
        """Close the modal and send the entry text to the callback."""
        first_value = self.entry_value.get()
        second_value = self.second_entry_value.get()
        self.close()
        if self.on_submit is not None:
            self.on_submit(first_value, second_value)

    def cancel(self, event: tk.Event | None = None) -> None:
        """Close the modal without submitting text."""
        self.close()

    def close(self) -> None:
        """Release the modal grab and remove the dialog."""
        try:
            self.window.grab_release()
        except tk.TclError:
            pass

        try:
            self.window.destroy()
        except tk.TclError:
            pass
