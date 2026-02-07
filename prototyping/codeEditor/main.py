from tkinter import *
from tkinter import ttk
import ast
from idlelib.percolator import Percolator
from idlelib.colorizer import ColorDelegator

ERROR_HEIGHT = 50
PARSE_DELAY_MS = 100

class Editor:
    def __init__(self, root: Tk):
        self.root = root
        self._parse_job = None
        self.save_btn = Button(root, text="Save Function", command=self.save_fcn)
        self.save_btn.pack(pady=10)
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
            background=self.background,
            foreground=self.normal,
            insertbackground=self.normal,
            relief=FLAT,
            borderwidth=30,
            font=self.font
        )

        # Insert some Standard Text into the Edit Area
        self.editArea.insert('1.0', """def my_function(t):
            return""")

        return
    

    def _from_rgb(self, rgb):
        """translates an rgb tuple of int to a tkinter friendly color code"""
        return "#%02x%02x%02x" % rgb
    
    def get_text(self):
        return self.editArea.get('1.0', END)
    
    def execute(self):
        exec(self.get_text(), {})

    def search_re(self, pattern, text, groupid=0):
        matches = []

        text = text.splitlines()
        for i, line in enumerate(text):
            for match in re.finditer(pattern, line):

                matches.append(
                    (f"{i + 1}.{match.start()}", f"{i + 1}.{match.end()}")
                )

        return matches

    # Register Changes made to the Editor Content
    def changes(self, event=None):
        global previousText

        # If actually no changes have been made stop / return the function
        if self.get_text() == previousText:
            return
        
        # Remove all tags so they can be redrawn
        for tag in self.editArea.tag_names():
            self.editArea.tag_remove(tag, "1.0", "end")
        
        # Add tags where the search_re function found the pattern
        i = 0
        for pattern, color in self.repl:
            for start, end in self.search_re(pattern, self.get_text()):
                self.editArea.tag_add(f'{i}', start, end)
                self.editArea.tag_config(f'{i}', foreground=color)

                i+=1
        
        previousText = self.get_text()




if __name__ == "__main__":
    root = Tk()
    root.title("Code Editor")
    root.geometry("900x600")
    editor = Editor(root)
    root.mainloop()
