# ncaa-basketball-scraper
API and GUI applications to get NCAA basketball stats from ESPN and NCAA.

This program downloads stats for games or players from ESPN.com, and gathers
them into a CSV file.

Included is a Tkinter GUI program and the Python source code. You can use
the command line version or develop it by following these steps:

## Windows setup

1. Install Python: https://www.python.org/downloads/
   Install at least version 3.10.
   You must check the options for tkinter as well as "update Path".

2. Create a virtual environment. Open a PowerShell window, navigate to this
   directory, and run `python3 -m venv venv`.

3. Activate the virtual environment: `.\venv\Scripts\Activate.ps1`

4. Install the required dependencies: `pip install -r requirements.txt`

## Development

1. Hack away. To run the command line version, simply run `python3 matchup.py`
   or `python3 player.py`.

2. To run the GUI version, run `python3 matchup_gui.py` or
   `python3 player_gui.py`.

3. To build the EXE version, run these commands:
  * For the matchup scraper:
   `pyinstaller ncaa_basketball/matchup_gui.py --paths=./ncaa_basketball
      --hidden-import babel.numbers --onefile --windowed`

  * For the player scraper:
   `pyinstaller ncaa_basketball/player_gui.py --paths=./ncaa_basketball
      --onefile --windowed`
