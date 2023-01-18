# espn-basketball-scraper
API and GUI applications to get NCAA basketball stats from the unofficial ESPN API.

This program downloads stats for games from ESPN.com, and gathers them into a
CSV file.

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

2. To run the GUI version, run `python3 gui.py`.

3. To build the EXE version, run this command:
   `pyinstaller gui.py --hidden-import matchup --paths=./ --hidden-import
   babel.numbers --onefile --windowed`
