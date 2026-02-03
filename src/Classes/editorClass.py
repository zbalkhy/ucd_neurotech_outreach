import tkinter as tk
import ctypes
import re
import os
import numpy as np


class Editor():
    def __init__(self, root):
        self.root = root
        self.frame = tk.Frame(self.root)

        # Define colors for the variouse types of tokens
        self.normal = self._from_rgb((234, 234, 234))
        self.keywords = self._from_rgb((234, 95, 95))
        self.comments = self._from_rgb((95, 234, 165))
        self.string = self._from_rgb((234, 162, 95))
        self.function = self._from_rgb((95, 211, 234))
        self.background = self._from_rgb((42, 42, 42))
        self.previousText = ''
        self.font = 'Consolas 15'
        self.functions = {}

        # assign colors to text types
        self.repl = [
            ['(^| )(False|None|True|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)($| )', self.keywords],
            ['".*?"', self.string],
            ['\'.*?\'', self.string],
            ['#.*?$', self.comments],]

        # import keywords are not handled yet but this regex should get us therequit
        # import_pattern = r'^\s*from\s+(\S+)\s+import\s+(\S+)(?:\s+as\s+(\S+))?'

        # Make the Text Widget
        # Add a hefty border width so we can achieve a little bit of padding
        self.editArea = tk.Text(
            root,
            background=self.background,
            foreground=self.normal,
            insertbackground=self.normal,
            relief=tk.FLAT,
            borderwidth=30,
            font=self.font
        )

        # Insert some Standard Text into the Edit Area
        self.editArea.insert('1.0', """def my_function(t):
                             return""")
        self.editArea.bind('<KeyRelease>', self.changes)

        # Place the Edit Area with the pack method
        self.editArea.pack(
            fill=tk.BOTH,
            expand=1
        )

        self.button_execute = tk.Button(
            master=root, text="execute_code", command=self.execute_python)
        self.button_execute.pack(side=tk.BOTTOM)
        self.changes()
        return

    # Translates an rgb tuple of int to a tkinter friendly color code
    def _from_rgb(self, rgb):
        return "#%02x%02x%02x" % rgb

    def execute_python(self):
        exec(self.get_text())

    def get_text(self):
        return self.editArea.get('1.0', tk.END)

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

        # If actually no changes have been made stop / return the function
        if self.get_text() == self.previousText:
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

                i += 1

        self.previousText = self.get_text()


if __name__ == "__main__":
    # Setup Tkinter
    root = tk.Tk()
    root.geometry('500x500')

    editor = Editor(root)
    root.mainloop()
