#!/usr/bin/env python3

import tkinter
from tkcalendar import DateEntry

import gui
import matchup


class MatchupGui(gui.Gui):
    def __init__(self, *args, **kwargs):
        gui.Gui.__init__(self, *args, **kwargs)
        self.title("NCAA Basketball ESPN matchup stats scrapper")

        self.start_label = tkinter.Label(self, text="Start date")
        self.start_label.grid(column=0, row=0)
        self.start_date = DateEntry(self)
        self.start_date.grid(column=1, row=0)

        self.end_label = tkinter.Label(self, text="End date")
        self.end_label.grid(column=0, row=1)
        self.end_date = DateEntry(self)
        self.end_date.grid(column=1, row=1)

    def run_program(self) -> None:
        matchup.compile_data(
            self.start_date.get_date(), self.end_date.get_date(), self.output
        )


if __name__ == "__main__":
    MatchupGui().mainloop()
