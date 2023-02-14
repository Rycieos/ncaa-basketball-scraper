#!/usr/bin/env python3

import tkinter
from typing import List

import gui
import player


class PlayerGui(gui.Gui):
    def __init__(self, *args, **kwargs):
        gui.Gui.__init__(self, *args, **kwargs)
        self.title("NCAA Basketball ESPN player stats scrapper")

        self.header_label = tkinter.Label(self, text="Stat groups to include:")
        self.header_label.grid(column=0, row=0)

        self.avg_enabled = tkinter.IntVar()
        self.avg_label = tkinter.Checkbutton(
            self, variable=self.avg_enabled, text="Season Averages"
        )
        self.avg_label.grid(column=0, row=1)

        self.total_enabled = tkinter.IntVar()
        self.total_label = tkinter.Checkbutton(
            self, variable=self.total_enabled, text="Season Totals"
        )
        self.total_label.grid(column=1, row=1)

        self.misc_enabled = tkinter.IntVar()
        self.misc_label = tkinter.Checkbutton(
            self, variable=self.misc_enabled, text="Season Misc Totals"
        )
        self.misc_label.grid(column=2, row=1)

    def run_program(self) -> None:
        group_filter: List[str] = list()

        if self.avg_enabled.get():
            group_filter.append("Season Averages")
        if self.total_enabled.get():
            group_filter.append("Season Totals")
        if self.misc_enabled.get():
            group_filter.append("Season Misc Totals")

        player.compile_data(self.output, group_filter)


if __name__ == "__main__":
    PlayerGui().mainloop()
