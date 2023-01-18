#!/usr/bin/env python3

import tkinter
import tkinter.filedialog
import matchup
import sys
from tkcalendar import DateEntry


class Gui(tkinter.Tk):
    def __init__(self, *args, **kwargs):
        tkinter.Tk.__init__(self, *args, **kwargs)
        self.title("NCAA Basketball ESPN stats scrapper")

        self.output = None

        self.start_label = tkinter.Label(self, text="Start date")
        self.start_label.grid(column=0, row=0)
        self.start_date = DateEntry(self)
        self.start_date.grid(column=1, row=0)

        self.end_label = tkinter.Label(self, text="End date")
        self.end_label.grid(column=0, row=1)
        self.end_date = DateEntry(self)
        self.end_date.grid(column=1, row=1)

        self.file_label = tkinter.Label(self, text="File: <none>")
        self.file_label.grid(column=0, row=2)
        self.file_picker = tkinter.Button(
            self, text="Choose file", command=self.choose_file
        )
        self.file_picker.grid(column=1, row=2)

        self.button = tkinter.Button(self, text="Run", command=self.run)
        self.button.grid(column=1, row=3)

        self.status = tkinter.Label(self, text="")
        self.status.grid(column=0, row=3)

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
            matchup.compile_data(
                self.start_date.get_date(), self.end_date.get_date(), self.output
            )
            self.status.configure(text="Complete.")
        except Exception as e:
            self.status.configure(text="Failed: {}".format(e))


if __name__ == "__main__":
    Gui().mainloop()
