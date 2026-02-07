from tkinter import *
from tkinter import ttk
import ast
from idlelib.percolator import Percolator
from idlelib.colorizer import ColorDelegator
from eventClass import EventClass, EventType

ERROR_HEIGHT = 50
PARSE_DELAY_MS = 100

class EditorClass(EventClass):
    def __init__(self, root: Tk):
        super().__init__()
        self.root = root
        self._parse_job = None
        self.error_bar = Frame(root, bg="#2b2b2b", height=0)
        self.error_bar.pack(side=BOTTOM, fill="x")
        self.error_bar.pack_propagate(False)

        self.errorArea = Text(
            self.error_bar,
            height=1,
            wrap="word",
            bg="#2b2b2b",
            fg="#ff1111",
            state="disabled",
        )

        scroll = ttk.Scrollbar(self.error_bar, orient="vertical", command=self.errorArea.yview)
        self.errorArea.configure(yscrollcommand=scroll.set)
        self.errorArea.pack(side=LEFT, fill="both", expand=True)
        scroll.pack(side=RIGHT, fill="y")

        self.editArea = Text(
            root,
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="#d4d4d4",
            selectbackground="#264f78",
            undo=True,
        )
        self.editArea.insert("1.0", "def my_function(t):\n\treturn\n")
        self.editArea.pack(side=TOP, fill="both", expand=True)

        self.cd = ColorDelegator()
        self.cd.tagdefs.update(
            {
                "COMMENT": {"foreground": "#6a9955"},
                "KEYWORD": {"foreground": "#569cd6"},
                "STRING": {"foreground": "#ce9178"},
                "BUILTIN": {"foreground": "#4ec9b0"},
                "DEFINITION": {"foreground": "#dcdcaa"},
            }
        )
        Percolator(self.editArea).insertfilter(self.cd)
        self.editArea.bind("<KeyRelease>", self.on_text_change)

        self.save_btn = Button(root, text="Save Function", command=self.save_fcn(self.get_text()))
        self.save_btn.pack(pady=5)

    def get_text(self) -> str:
        return self.editArea.get("1.0", "end-1c")

    def execute(self):
        exec(self.get_text(), {})

    def save_fcn(self, txt: str):
        fcns = {}
        tree = ast.parse(txt)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                fcns[node.name] = ast.get_source_segment(txt, node)
        self.notify(fcns, EventType.FUNCTIONUPDATE)

    def on_text_change(self, event=None):
        if self._parse_job is not None:
            self.root.after_cancel(self._parse_job)
        self._parse_job = self.root.after(PARSE_DELAY_MS, lambda: self.check_syntax(self.get_text()))

    def check_syntax(self, src: str):
        try:
            ast.parse(src)
            self.clear_error()
        except SyntaxError as e:
            lineno = e.lineno or 1
            msg = e.msg or "Syntax error"
            self.show_error(f"Line {lineno}: {msg}")

    def show_error(self, msg: str):
        self.error_bar.configure(height=ERROR_HEIGHT)
        self.errorArea.config(state="normal")
        self.errorArea.delete("1.0", "end")
        self.errorArea.insert("1.0", msg)
        self.errorArea.config(state="disabled")

    def clear_error(self):
        self.errorArea.config(state="normal")
        self.errorArea.delete("1.0", "end")
        self.errorArea.config(state="disabled")
        self.error_bar.configure(height=0)

if __name__ == "__main__":
    root = Tk()
    root.title("Code Editor")
    root.geometry("900x600")
    editor = EditorClass(root)
    root.mainloop()
