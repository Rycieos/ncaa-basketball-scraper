#!/usr/bin/env python3

import tkinter
import tkinter.filedialog


class Gui(tkinter.Tk):
    def __init__(self, *args, **kwargs):
        tkinter.Tk.__init__(self, *args, **kwargs)

        self.output = None
        self.program = None

        self.file_label = tkinter.Label(self, text="File: <none>")
        self.file_label.grid(column=0, row=10)
        self.file_picker = tkinter.Button(
            self, text="Choose file", command=self.choose_file
        )
        self.file_picker.grid(column=1, row=10)

        self.button = tkinter.Button(self, text="Run", command=self.run)
        self.button.grid(column=1, row=11)

        self.status = tkinter.Label(self, text="")
        self.status.grid(column=0, row=11)

    def choose_file(self):
        self.output = tkinter.filedialog.asksaveasfilename(defaultextension=".csv")
        self.file_label.configure(text="File: {}".format(self.output))

    def run(self):
        if self.output is None:
            self.status.configure(text="Need to choose output!")
            return

        self.status.configure(text="Running...")
        self.update_idletasks()  # Allow tkinter to update gui.

        try:
            self.run_program()
            self.status.configure(text="Complete.")
        except Exception as e:
            self.status.configure(text="Failed: {}".format(e))
