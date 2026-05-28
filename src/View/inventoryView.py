import tkinter as tk

from Classes.eventClass import EventClass, EventType
from ViewModel.inventoryViewModel import InventoryViewModel


class InventoryView(EventClass):
    STREAM = "stream"
    DATASET = "dataset"
    CLASSIFIER = "classifier"

    LIGHT_THEME = {
        "BACKGROUND": "#f4f5f7",
        "SECTION_BACKGROUND": "#ffffff",
        "CARD_BACKGROUND": "#ffffff",
        "CARD_HOVER_BACKGROUND": "#eef4ff",
        "BORDER": "#d9dee8",
        "HOVER_BORDER": "#7aa7e6",
        "TEXT": "#1f2937",
        "MUTED_TEXT": "#687385",
    }
    DARK_THEME = {
        "BACKGROUND": "#161a20",
        "SECTION_BACKGROUND": "#20252d",
        "CARD_BACKGROUND": "#282e38",
        "CARD_HOVER_BACKGROUND": "#303947",
        "BORDER": "#3b4452",
        "HOVER_BORDER": "#77a9ee",
        "TEXT": "#edf2f7",
        "MUTED_TEXT": "#a7b1bf",
    }
    RUNNING = "#2f9e44"
    STOPPED = "#9aa4b2"
    DATASET_ACCENT = "#5b7cfa"
    CLASSIFIER_ACCENT = "#cc7a00"
    DELETE = "#b00020"
    CARD_MIN_WIDTH = 155
    CARD_GAP = 8
    CONTROL_MASK = 0x0004

    def __init__(self, frame: tk.Frame, view_model: InventoryViewModel):
        super().__init__()

        self.view_model = view_model
        self.subscribe_to_subject(self.view_model.user_model)
        self.frame: tk.Frame = frame
        self._context_menu = None
        self.section_frames = {}
        self.card_frames = {}
        self.section_columns = {}

        self._set_theme_colors()
        self._build_layout()
        self.refresh_all()

    def _set_theme_colors(self) -> None:
        palette = self.DARK_THEME if self._is_dark_theme() else self.LIGHT_THEME
        for color_name, color_value in palette.items():
            setattr(self, color_name, color_value)

    def _is_dark_theme(self) -> bool:
        try:
            red, green, blue = self.frame.winfo_rgb(
                self.frame.cget("background"))
        except tk.TclError:
            return False

        weighted_red = 0.2126 * red
        weighted_green = 0.7152 * green
        weighted_blue = 0.0722 * blue
        luminance = (weighted_red + weighted_green + weighted_blue) / 65535
        return luminance < 0.5

    def _build_layout(self) -> None:
        """Build a scrollable inventory area with one card grid per section."""
        self.frame.configure(bg=self.BACKGROUND)
        self.inner_frame = tk.Frame(self.frame, bg=self.BACKGROUND)
        self.inner_frame.pack(fill="both", expand=True, padx=8, pady=8)
        self.inner_frame.rowconfigure(0, weight=1)
        self.inner_frame.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            self.inner_frame,
            bg=self.BACKGROUND,
            borderwidth=0,
            highlightthickness=0)
        self.scrollbar = tk.Scrollbar(
            self.inner_frame,
            orient="vertical",
            command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollable_frame = tk.Frame(self.canvas, bg=self.BACKGROUND)
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor="nw")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda event: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.scrollable_frame.columnconfigure(0, weight=1)

        sections = [
            (self.STREAM, "Streams"),
            (self.DATASET, "Datasets"),
            (self.CLASSIFIER, "Classifiers"),
        ]
        for row, (entity_type, title) in enumerate(sections):
            section = tk.Frame(
                self.scrollable_frame,
                bg=self.SECTION_BACKGROUND,
                highlightbackground=self.BORDER,
                highlightthickness=1)
            section.grid(row=row, column=0, sticky="ew", pady=(0, 10))
            section.columnconfigure(0, weight=1)

            header = tk.Label(
                section,
                text=title,
                bg=self.SECTION_BACKGROUND,
                fg=self.TEXT,
                font=("TkDefaultFont", 10, "bold"),
                anchor="w",
                padx=10,
                pady=7)
            header.grid(row=0, column=0, sticky="ew")

            body = tk.Frame(section, bg=self.SECTION_BACKGROUND)
            body.grid(row=1, column=0, sticky="ew", padx=6, pady=(0, 8))
            body.bind(
                "<Configure>",
                lambda event, item_type=entity_type:
                    self._on_section_configure(event, item_type))

            self.section_frames[entity_type] = body
            self.card_frames[entity_type] = []
            self.section_columns[entity_type] = 0

    def refresh_all(self) -> None:
        self._refresh_section(self.STREAM)
        self._refresh_section(self.DATASET)
        self._refresh_section(self.CLASSIFIER)

    def _refresh_section(self, entity_type: str) -> None:
        section_frame = self.section_frames[entity_type]
        self._clear_section(section_frame)
        self._reset_section_columns(entity_type)
        self.card_frames[entity_type] = []

        names = self._get_entity_names(entity_type)
        if not names:
            empty_label = tk.Label(
                section_frame,
                text=f"No {self._entity_label(entity_type).lower()}s",
                bg=self.SECTION_BACKGROUND,
                fg=self.MUTED_TEXT,
                anchor="w",
                padx=6,
                pady=8)
            empty_label.grid(row=0, column=0, sticky="ew")
            section_frame.columnconfigure(0, weight=1)
            return

        for name in names:
            card = self._create_entity_card(section_frame, entity_type, name)
            self.card_frames[entity_type].append(card)

        self._layout_cards(entity_type, force=True)

    def _create_entity_card(
            self,
            parent: tk.Frame,
            entity_type: str,
            name: str) -> tk.Frame:
        accent, detail_text = self._card_detail(entity_type, name)
        cursor = "hand2" if entity_type in [
            self.STREAM,
            self.CLASSIFIER,
        ] else "arrow"

        card = tk.Frame(
            parent,
            bg=self.CARD_BACKGROUND,
            cursor=cursor,
            height=68,
            highlightbackground=self.BORDER,
            highlightthickness=1)
        card.grid_propagate(False)
        card.columnconfigure(1, weight=1)
        card.rowconfigure(0, weight=1)

        indicator = tk.Frame(card, bg=accent, width=6, cursor=cursor)
        indicator.grid(row=0, column=0, rowspan=2, sticky="ns")

        name_label = tk.Label(
            card,
            text=name,
            bg=self.CARD_BACKGROUND,
            fg=self.TEXT,
            cursor=cursor,
            font=("TkDefaultFont", 9, "bold"),
            anchor="w",
            justify="left")
        name_label.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(9, 8),
            pady=(8, 1))
        name_label.bind(
            "<Configure>",
            lambda event, label=name_label:
                label.configure(wraplength=max(event.width - 4, 60)))

        detail_label = tk.Label(
            card,
            text=detail_text,
            bg=self.CARD_BACKGROUND,
            fg=self.MUTED_TEXT,
            cursor=cursor,
            font=("TkDefaultFont", 8),
            anchor="w")
        detail_label.grid(
            row=1,
            column=1,
            sticky="ew",
            padx=(9, 8),
            pady=(0, 8))

        text_widgets = [name_label, detail_label]
        click_widgets = [card, indicator, name_label, detail_label]
        for widget in click_widgets:
            self._bind_card_context_menu(widget, entity_type, name)
            if entity_type in [self.STREAM, self.CLASSIFIER]:
                widget.bind(
                    "<Button-1>",
                    lambda event, item_type=entity_type, item_name=name:
                        self._on_card_click(event, item_type, item_name))
                widget.bind(
                    "<Enter>",
                    lambda event, card_widget=card, labels=text_widgets:
                        self._set_card_colors(
                            card_widget,
                            labels,
                            self.CARD_HOVER_BACKGROUND,
                            self.HOVER_BORDER))
                widget.bind(
                    "<Leave>",
                    lambda event, card_widget=card, labels=text_widgets:
                        self._set_card_colors(
                            card_widget,
                            labels,
                            self.CARD_BACKGROUND,
                            self.BORDER))

        return card

    def _card_detail(self, entity_type: str, name: str) -> tuple[str, str]:
        if entity_type == self.STREAM:
            stream = self.view_model.user_model.get_stream(name)
            is_running = stream is not None and stream.is_alive()
            if is_running:
                return self.RUNNING, "Running"
            return self.STOPPED, "Stopped"
        if entity_type == self.DATASET:
            return self.DATASET_ACCENT, "Dataset"
        return self.CLASSIFIER_ACCENT, "Classifier"

    def _set_card_colors(
            self,
            card: tk.Frame,
            labels: list[tk.Label],
            background: str,
            border: str) -> None:
        card.configure(bg=background, highlightbackground=border)
        for label in labels:
            label.configure(bg=background)

    def _on_card_click(
            self,
            event: tk.Event,
            entity_type: str,
            name: str) -> str | None:
        if event.state & self.CONTROL_MASK:
            return "break"
        if entity_type == self.STREAM:
            self.on_stream_click(name)
            return "break"
        if entity_type == self.CLASSIFIER:
            self.on_classifier_click(name)
            return "break"
        return None

    def on_stream_click(self, item_name: str) -> None:
        self.view_model.toggle_stream(item_name)

    def on_classifier_click(self, item_name: str) -> None:
        stream = self.view_model.user_model.get_stream(item_name)
        if stream is None or not stream.is_alive():
            self.view_model.train_classifier(item_name)

    def _bind_card_context_menu(
            self,
            widget: tk.Widget,
            entity_type: str,
            name: str) -> None:
        widget.bind(
            "<Button-3>",
            lambda event, item_type=entity_type, item_name=name:
                self._on_context_menu(event, item_type, item_name))
        widget.bind(
            "<Button-2>",
            lambda event, item_type=entity_type, item_name=name:
                self._on_context_menu(event, item_type, item_name))
        widget.bind(
            "<Control-Button-1>",
            lambda event, item_type=entity_type, item_name=name:
                self._on_context_menu(event, item_type, item_name))

    def _on_context_menu(
            self,
            event: tk.Event,
            entity_type: str,
            item_name: str) -> str:
        """Show a context menu that stays open until Close Menu is clicked."""
        self._close_context_menu()

        menu = tk.Toplevel(self.frame)
        menu.wm_overrideredirect(True)
        menu.lift()
        menu.attributes("-topmost", True)
        menu.geometry(f"+{event.x_root + 25}+{event.y_root}")
        menu.grab_set_global()

        btn_rename = tk.Button(
            menu,
            text="Rename",
            command=lambda: self._open_rename_and_close(
                menu,
                entity_type,
                item_name))
        btn_rename.pack(fill="x", padx=4, pady=2)

        btn_delete = tk.Button(
            menu,
            text="Delete",
            fg=self.DELETE,
            command=lambda: self._on_delete_and_close(
                menu,
                entity_type,
                item_name))
        btn_delete.pack(fill="x", padx=4, pady=2)

        btn_close = tk.Button(
            menu,
            text="Close Menu",
            bg="#ddd",
            command=self._close_context_menu)
        btn_close.pack(fill="x", padx=4, pady=2)

        self._context_menu = menu
        return "break"

    def _close_context_menu(self) -> None:
        if getattr(self, "_context_menu", None):
            try:
                self._context_menu.grab_release()
                self._context_menu.destroy()
            except tk.TclError:
                pass
            self._context_menu = None

    def _on_delete_and_close(
            self,
            menu: tk.Toplevel,
            entity_type: str,
            name: str) -> None:
        self._close_context_menu()

        confirm = tk.Toplevel(self.frame)
        confirm.title("Confirm Delete")
        confirm.transient(self.frame)
        confirm.geometry("+400+250")

        tk.Label(confirm, text=f"Delete '{name}'?", padx=10, pady=10).pack()

        btn_frame = tk.Frame(confirm)
        btn_frame.pack(pady=5)

        def do_delete() -> None:
            success = self._delete_entity(entity_type, name)
            confirm.destroy()
            if not success:
                print(f"[Inventory] delete failed for '{name}'")

        tk.Button(
            btn_frame,
            text="Delete",
            fg=self.DELETE,
            command=do_delete).pack(side="left", padx=5)
        tk.Button(
            btn_frame,
            text="Cancel",
            command=confirm.destroy).pack(side="left", padx=5)

    def _open_rename_and_close(
            self,
            menu: tk.Toplevel,
            entity_type: str,
            current_display: str) -> None:
        self._close_context_menu()
        self._open_rename_popup(entity_type, current_display)

    def _open_rename_popup(self, entity_type: str, old_name: str) -> None:
        popup = tk.Toplevel(self.frame)
        popup.title(f"Rename {self._entity_label(entity_type)}: {old_name}")
        popup.transient(self.frame)

        tk.Label(popup, text="Old Name:").grid(
            row=0, column=0, padx=6, pady=6, sticky="w")
        tk.Label(popup, text=old_name).grid(
            row=0, column=1, padx=6, pady=6, sticky="w")

        tk.Label(popup, text="New Name:").grid(
            row=1, column=0, padx=6, pady=6, sticky="w")
        new_name_entry = tk.Entry(popup)
        new_name_entry.grid(row=1, column=1, padx=6, pady=6, sticky="ew")
        new_name_entry.insert(0, old_name)
        new_name_entry.focus_set()

        def apply_new_name(event: tk.Event | None = None) -> None:
            new_name = new_name_entry.get().strip()
            if not new_name:
                return
            success = self._rename_entity(entity_type, old_name, new_name)
            if not success:
                print(f"[Inventory] rename failed for '{old_name}'")
            popup.destroy()

        tk.Button(popup, text="Apply", command=apply_new_name).grid(
            row=2, column=0, columnspan=2, pady=8)
        popup.bind("<Return>", apply_new_name)
        popup.columnconfigure(1, weight=1)

    def _rename_entity(
            self,
            entity_type: str,
            old_name: str,
            new_name: str) -> bool:
        if entity_type == self.STREAM:
            return self.view_model.rename_stream(old_name, new_name)
        if entity_type == self.DATASET:
            return self.view_model.rename_dataset(old_name, new_name)
        if entity_type == self.CLASSIFIER:
            return self.view_model.rename_classifier(old_name, new_name)
        return False

    def _delete_entity(self, entity_type: str, name: str) -> bool:
        if entity_type == self.STREAM:
            return self.view_model.delete_stream_by_name(name)
        if entity_type == self.DATASET:
            return self.view_model.delete_dataset_by_name(name)
        if entity_type == self.CLASSIFIER:
            return self.view_model.delete_classifier_by_name(name)
        return False

    def _get_entity_names(self, entity_type: str) -> list[str]:
        if entity_type == self.STREAM:
            return self.view_model.get_stream_names()
        if entity_type == self.DATASET:
            return self.view_model.get_dataset_names()
        if entity_type == self.CLASSIFIER:
            return self.view_model.get_classifier_names()
        return []

    def _entity_label(self, entity_type: str) -> str:
        labels = {
            self.STREAM: "Stream",
            self.DATASET: "Dataset",
            self.CLASSIFIER: "Classifier",
        }
        return labels.get(entity_type, "Item")

    def _clear_section(self, section_frame: tk.Frame) -> None:
        for child in section_frame.winfo_children():
            child.destroy()

    def _reset_section_columns(self, entity_type: str) -> None:
        section_frame = self.section_frames[entity_type]
        previous_columns = max(self.section_columns.get(entity_type, 1), 1)
        for column in range(previous_columns):
            section_frame.columnconfigure(column, weight=0, minsize=0)
        self.section_columns[entity_type] = 0

    def _on_canvas_configure(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.canvas_window, width=event.width)
        self._layout_all_sections()

    def _on_section_configure(
            self,
            event: tk.Event,
            entity_type: str) -> None:
        new_columns = self._column_count(event.width)
        if self.section_columns.get(entity_type) != new_columns:
            self._layout_cards(entity_type, columns=new_columns)

    def _layout_all_sections(self) -> None:
        for entity_type in self.section_frames:
            self._layout_cards(entity_type)

    def _layout_cards(
            self,
            entity_type: str,
            columns: int | None = None,
            force: bool = False) -> None:
        cards = self.card_frames.get(entity_type, [])
        if not cards:
            return

        section_frame = self.section_frames[entity_type]
        if columns is None:
            columns = self._column_count(section_frame.winfo_width())
        if not force and self.section_columns.get(entity_type) == columns:
            return

        previous_columns = max(self.section_columns.get(entity_type, 1), 1)
        for column in range(max(previous_columns, columns)):
            section_frame.columnconfigure(column, weight=0, minsize=0)

        for column in range(columns):
            section_frame.columnconfigure(
                column,
                weight=1,
                minsize=self.CARD_MIN_WIDTH)

        for index, card in enumerate(cards):
            row = index // columns
            column = index % columns
            card.grid(
                row=row,
                column=column,
                sticky="ew",
                padx=self.CARD_GAP // 2,
                pady=self.CARD_GAP // 2)

        self.section_columns[entity_type] = columns

    def _column_count(self, width: int) -> int:
        if width <= 1:
            width = self.frame.winfo_width()
        if width <= 1:
            return 1
        return max(1, width // (self.CARD_MIN_WIDTH + self.CARD_GAP))

    def add_item(self, item: str) -> None:
        self.refresh_all()

    def remove_item(self, item: str) -> None:
        self.refresh_all()

    def on_notify(self, eventData, event) -> None:
        if event in [EventType.STREAMUPDATE, EventType.STREAMTOGGLED]:
            self._refresh_section(self.STREAM)
        elif event == EventType.DATASETUPDATE:
            self._refresh_section(self.DATASET)
        elif event == EventType.CLASSIFIERUPDATE:
            self._refresh_section(self.CLASSIFIER)
        return
