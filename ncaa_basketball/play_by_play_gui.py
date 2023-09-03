#!/usr/bin/env python3

import tkinter
from tkcalendar import DateEntry

import ncaa_basketball.gui as gui
import ncaa_basketball.play_by_play as pbp


class PbPGui(gui.Gui):
    def __init__(self, *args, **kwargs):
        gui.Gui.__init__(self, *args, **kwargs)
        self.title("NCAA Basketball play by play stats scrapper")

        self.start_label = tkinter.Label(self, text="Start date")
        self.start_label.grid(column=0, row=0)
        self.start_date = DateEntry(self)
        self.start_date.grid(column=1, row=0)

        self.end_label = tkinter.Label(self, text="End date")
        self.end_label.grid(column=0, row=1)
        self.end_date = DateEntry(self)
        self.end_date.grid(column=1, row=1)

        self.div_label = tkinter.Label(self, text="Division")
        self.div_label.grid(column=0, row=2)
        self.div_var = tkinter.StringVar(self)
        self.div_picker = tkinter.OptionMenu(self, self.div_var, "d1", "d2", "d3")
        self.div_picker.grid(column=1, row=2)

        self.header_label = tkinter.Label(self, text="Options:")
        self.header_label.grid(column=0, row=3)

        self.mirror_enabled = tkinter.BooleanVar()
        self.mirror_label = tkinter.Checkbutton(
            self, variable=self.mirror_enabled, text="Mirror events"
        )
        self.mirror_label.grid(column=1, row=3)

    def run_program(self) -> None:
        pbp.compile_data(
            self.div_var.get(),
            self.start_date.get_date(),
            self.end_date.get_date(),
            self.output,
            mirror=self.mirror_enabled.get(),
        )


if __name__ == "__main__":
    PbPGui().mainloop()
