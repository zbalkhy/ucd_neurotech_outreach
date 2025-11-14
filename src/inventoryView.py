import tkinter as tk
import tkinter.ttk as ttk
from eventClass import *
from inventoryViewModel import InventoryViewModel
from common import create_grid

class InventoryView(EventClass):
    def __init__(self, frame: tk.Frame, view_model: InventoryViewModel):
        super().__init__()

        self.view_model = view_model
        self.subscribe_to_subject(self.view_model.user_model)
        # set class variables
        self.frame: tk.Frame = frame
        style = ttk.Style(self.frame)

        # Disable highlight on the treeview
        style.map("Treeview",
        background=[
            ('selected', 'invalid', 'yellow'),('pressed', 'focus', 'yellow')
        ])
        # grab png image for stream running icon
        self.stream_running_icon = tk.PhotoImage(file="/Users/zacariabalkhy/Downloads/explorer/folder.png")

        # Inventory Label
        #self.inventory_label = tk.Label(self.frame, text="Inventory")
        #self.inventory_label.pack(pady=10)

        self.views = [['Inventory'], ['Streams'], ['Datasets']]
        self.frames = create_grid(self.frame,3,1, self.views, resize=False)

        # Inventory Label
        #self.inventory_label = tk.Label(self.frames[0][0], text="Inventory")
        #self.inventory_label.pack(pady=10)
        
        # Stream tree
        self.stream_tree = ttk.Treeview(self.frames[1][0], show='tree', columns=("start/stop"))
        self.stream_tree.column("start/stop", width=50)
        self.bind_context_menu(self.stream_tree)
        self.stream_tree.pack(anchor=tk.NW)
        self.populate_streams()
        # bind click event to toggle stream start/stop
        self.stream_tree.bind("<Button-1>", self.on_click)

        # Dataset tree
        self.dataset_tree = ttk.Treeview(self.frames[2][0], show='tree')
        self.bind_context_menu(self.dataset_tree)
        self.dataset_tree.pack(anchor=tk.NW)
        self.populate_datasets()    

    def add_item(self, item: str) -> None:
        self.inventory_listbox.insert(tk.END, item)

    def remove_item(self, item: str) -> None:
        items = self.inventory_listbox.get(0, tk.END)
        if item in items:
            index = items.index(item)
            self.inventory_listbox.delete(index)
    
    def populate_streams(self) -> None:
        self.stream_names = self.view_model.get_stream_names()
        for i in range(len(self.stream_names)):
            self.stream_tree.insert("", "end", text=self.stream_names[i], values=("start"))
        return
    
    def populate_datasets(self) -> None:
        self.data_sets = self.view_model.get_dataset_names()
        for i in range(len(self.data_sets)):
            self.dataset_tree.insert("", "end", text=self.data_sets[i])
        return
    
    def on_click(self, event) -> None:
        item = self.stream_tree.identify('item',event.x,event.y)
        item_name = self.stream_tree.item(item, "text")
        self.view_model.toggle_stream(item_name)
        if self.stream_tree.item(item, "image"):
            self.stream_tree.item(item, image="", values=("start"))
        else:
            self.stream_tree.item(item, image=self.stream_running_icon, values=("stop"))
        return
    
    def bind_context_menu(self, widget) -> None:
        widget.bind("<Button-3>", self._on_stream_context_menu)  # Windows right-click
        widget.bind("<Button-2>", self._on_stream_context_menu)  # Mac right-click
        widget.bind("<Control-Button-1>", self._on_stream_context_menu)  # mac Ctrl-click
        return
    
    # ------------------------------
    # Right-click context + rename
    # ------------------------------
    def _on_stream_context_menu(self, event):
        """Show a context menu that stays open until Close Menu is clicked."""
        widget = event.widget
        item_iid = widget.identify('item',event.x,event.y)
        item_name = widget.item(item_iid, 'text')
        
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
                            command=lambda: self._open_rename_and_close(menu, widget, item_name))
        btn_rename.pack(fill="x", padx=4, pady=2)

        btn_delete = tk.Button(menu, text="Delete", fg="red",
                            command=lambda: self._on_delete_and_close(menu, widget, item_name))
        btn_delete.pack(fill="x", padx=4, pady=2)

        btn_close = tk.Button(menu, text="Close Menu", bg="#ddd",
                            command=self._close_context_menu)
        btn_close.pack(fill="x", padx=4, pady=2)

        # Save reference
        self._context_menu = menu

    def _close_context_menu(self):
        if getattr(self, "_context_menu", None):
            try:
                self._context_menu.grab_release()
                self._context_menu.destroy()
            except Exception:
                pass
            self._context_menu = None
    
    def _on_delete_and_close(self, menu, widget, name):
        """Delete the selected stream safely and clear the plot if needed."""
        self._close_context_menu()

        confirm = tk.Toplevel(self.frame)
        confirm.title("Confirm Delete")
        confirm.transient(self.frame)
        confirm.geometry("+400+250")

        tk.Label(confirm, text=f"Delete '{name}'?", padx=10, pady=10).pack()

        btn_frame = tk.Frame(confirm)
        btn_frame.pack(pady=5)

        def do_delete():
            match widget:
                case self.stream_tree:
                    success = self.view_model.delete_stream_by_name(name)
                case self.dataset_tree:
                    success = self.view_model.delete_dataset_by_name(name)
            confirm.destroy()
            if not success:
                print(f"[Inventory] delete failed for '{name}'")

        tk.Button(btn_frame, text="Delete", fg="red", command=do_delete).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancel", command=confirm.destroy).pack(side="left", padx=5)
    
    def _open_rename_and_close(self, menu, widget, current_display):
        self._close_context_menu()
        self._open_rename_popup(widget, current_display)
    
    def _open_rename_popup(self, widget, old_name):
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
            match widget:
                case self.stream_tree:
                    success = self.view_model.rename_stream(old_name, new_name)
                case self.dataset_tree:
                    success = self.view_model.rename_dataset(old_name, new_name)
            if not success:
                print(f"[Inventory] delete failed for '{old_name}'")
            popup.grab_release()
            popup.destroy()

        tk.Button(popup, text="Apply", command=apply_new_name).grid(row=2, column=0, columnspan=2, pady=8)
        popup.columnconfigure(1, weight=1)

    def on_notify(self, eventData, event) -> None:
        if event == EventType.STREAMUPDATE:
            # refresh stream list
            for child in self.stream_tree.get_children():
                self.stream_tree.delete(child)
            self.populate_streams()
        elif event == EventType.DATASETUPDATE:
            # refresh dataset list
            for child in self.dataset_tree.get_children():
                self.dataset_tree.delete(child)
            self.populate_datasets()
        return 