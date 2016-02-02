import curses
from curses import COLOR_WHITE, COLOR_GREEN, COLOR_BLUE, COLOR_CYAN, \
    COLOR_BLACK, COLOR_MAGENTA

from ui.cli_windows import StringWindow, EditorWindow, \
    MenuWindow, MenuTuple

from itertools import cycle
from time import sleep
from config import config

import queue
import logging
import logging.handlers
import sys


# can't rely on curses to find tab, enter, etc.
KEY_TAB = 9

# name some colors (foreground/background pairs) actually defined later through curses.init_pair
BASIC = 0  # not editable
TITLE_ACTIVE = 1
TITLE_INACTIVE = 2
MENU_MESSAGE = 3


class StdOutWrapper():
    """
    Can print() to curses using this class to replace sys.stdout

    Notes
    -----
    You can output mystdout.get_text() in a ncurses widget in runtime
    """
    def __init__(self):
        """ Initialises the string stream object.

        Parameters
        ----------
            text : string
                A string to be written to the steam.
        """
        self.text = ""
        self.updated = False

    def write(self, txt):
        self.text += txt
        self.text = '\n'.join(self.text.split('\n')[-1000:])
        self.updated = True

    def get_text(self, beg=0, end=-1):
        """
        Return a string. Retrive sepcific rows from the stream.

        Row separater is \n by default.
        """
        self.updated = False
        return '\n'.join(self.text.split('\n')[beg:end])

    def get_last_rows(self, n=20):
        """
        Return a list. Retreive specific rows from the stream.

        """
        self.updated = False
        return self.text.split('\n')[- n - 1:]


class CommandLineInterface():
    """
    Command line user interface for FincLab.

    Notes
    -----
        Trigger .run() to execute.

        Use self.stream.write() to post strings to the output pane.
    """

    def __init__(self, event_queue=queue.Queue(), config=config):
        """
        Initialise the interface.

        Parameters
        ----------
            event_queue : queue.Queue()
                The event queue for the event-driven system. Log (and message) events will be read from the queue and printed to the User Interface.
        """
        self.event_queue = event_queue
        self.sleep_time = float(config['ui']['refresh_time'])
        self.auto_scale = config.getboolean('ui', 'auto')
        self.stream = StdOutWrapper()

    def start_listener(self):
        """ Start the logger listener to take log events from the queue.
        Only starts after initialising the UI.
        """
        # Log listener
        self.handler = logging.StreamHandler()
        self.listener = logging.handlers.QueueListener(self.event_queue, self.handler)
        self.listener.start()

    def _refresh(self):
        """
        Refreshes the screen.using a loop, and captures key pressings to trigger different behaviours.
        """
        while True:
            # asynchronously try to get the key the user pressed
            key = self.stdscr.getch()
            if key == curses.ERR:
                # no key was pressed.  Do house-keeping
                dirtied = 0
                for win in self.windows:
                    dirtied += win.dirty
                    win.update()
                # if dirtied:
                self.stdscr.refresh()

                # Refresh output pane
                if self.stream.updated:
                    output = self.stream.get_last_rows(self.lines_in_output_pane)
                    self.pane_output.refresh_pane(output)

                sleep(self.sleep_time)  # Refresh rate = 10 times per second

            elif key == KEY_TAB:
                # cycle input window
                self.active_window.draw_border()  # uses window default
                self.active_window = next(self.input_windows)
                self.active_window.draw_border(TITLE_ACTIVE)
            else:
                # every other key gets processed by the active input window
                self.active_window.process_key(key)

    def run(self):
        """
        Launch the interface.
        """
        # Set up screen.  Try/except to make sure the terminal gets put back together no matter what happens
        try:

            sys.stdout = self.stream
            sys.stderr = self.stream

            self.stdscr = curses.initscr()
            curses.start_color()
            curses.noecho()  # let input windows handle drawing characters to the screen
            curses.cbreak()  # enable key press asynch
            self.stdscr.nodelay(1)  # enable immediate time out (don't wait for keys at all)
            self.stdscr.keypad(1)  # enable enter, tab, and other keys

            # Set initial palette
            curses.init_pair(TITLE_ACTIVE, COLOR_BLUE, COLOR_BLACK)
            curses.init_pair(TITLE_INACTIVE, COLOR_WHITE, COLOR_BLACK)
            curses.init_pair(MENU_MESSAGE, COLOR_MAGENTA, COLOR_BLACK)

            # run while wrapped in this try/except
            self._layout()

            # Creates an internal logger
            self._create_logger()

            # Starts the logger listener
            self.start_listener()  # start the listener to take log events from the queue (only after the UI has initialised)

            # Ininite loop to refresh the interface
            self._refresh()

        except Exception:
            # put the terminal back in it's normal mode before raising the error
            curses.nocbreak()
            self.stdscr.keypad(0)
            curses.echo()
            curses.endwin()
            raise
        finally:
            curses.nocbreak()
            self.stdscr.keypad(0)
            curses.echo()
            curses.endwin()

            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            sys.stdout.write(self.stream.get_text())

    def _layout(self):
        """ Core of the Commandline User Interface. Defines the layout of the interface.
        """

        # Manual tiling
        (maxy, maxx) = self.stdscr.getmaxyx()

        if self.auto_scale:
            splitx = int(maxx * .3)
            splity = int(maxy * .7)
        else:
            splitx = 25
            splity = maxy - 10

        # Title height
        title_height = 7

        # initialize windows
        # specify Upper left corner, size, title, color scheme and border/no-border
        self.main_border = StringWindow((0, 0), (maxx, maxy), ' FincLab Ver 0.1 ', TITLE_INACTIVE)
        self.pane_output = StringWindow((splitx, title_height + 1), (maxx - splitx - 1, splity - title_height - 1), 'Output', TITLE_INACTIVE)
        self.pane_menu = MenuWindow((1, title_height + 1), (splitx - 1, splity - title_height - 1), 'Menu', TITLE_INACTIVE)
        self.pane_command = EditorWindow((splitx, splity), (maxx - splitx - 1, maxy - splity - 1), 'Type Commands...', palette=TITLE_INACTIVE, callback=self.pane_output.add_str)
        self.pane_status = StringWindow((1, splity), (splitx - 1, maxy - splity - 1), 'Status', palette=TITLE_INACTIVE)

        self.lines_in_output_pane = splity - title_height - 3

        # Set menu options with corrisponding callbacks
        menu_actions = [
            MenuTuple("Say 'Hi'", (self.pane_output.add_str, 'Hello from Mars!', MENU_MESSAGE)),
            MenuTuple('Colour - Default', (curses.init_pair, TITLE_INACTIVE, COLOR_WHITE, COLOR_BLACK)),
            MenuTuple('Colour - Cyan', (curses.init_pair, TITLE_INACTIVE, COLOR_CYAN, COLOR_BLACK)),
            MenuTuple('Colour - Green', (curses.init_pair, TITLE_INACTIVE, COLOR_GREEN, COLOR_BLACK))]
        self.pane_menu.set_menu(menu_actions)

        # Put all the windows in a list so they can be updated together
        self.windows = [self.main_border, self.pane_output, self.pane_menu, self.pane_command, self.pane_status]

        # create input window cycling an input window must have a process_key(key) method
        self.input_windows = cycle([self.pane_menu, self.pane_command])
        self.active_window = next(self.input_windows)
        self.active_window.draw_border(TITLE_ACTIVE)

        # Add titles and other texts
        self.main_border.add_str("  FincLab Event-Driven Live-Trading / Backtesting Engine")
        self.main_border.add_str(" ")
        self.main_border.add_str("  Author: Peter Lee (mr.peter.lee@hotmail.com)")
        self.main_border.add_str(" ")
        self.main_border.add_str("  Instrctions:")
        self.main_border.add_str('      - Please configure program settings in the "config.ini"')
        self.main_border.add_str("      - End-of-day data will be downloaded automatically if not found.")
        self.pane_status.add_str("Press <TAB> to switch pane")
        self.pane_status.add_str("[Engine status]: Backtesting")

    def _create_logger(self):
        """
        Logger that utilises the queue handler.
        """
        level = logging.DEBUG
        self.logger = logging.getLogger("FincLab.UI")
        self.logger.setLevel(level)
        formatter = logging.Formatter(fmt="%(levelname)-8s %(message)s")
        formatter = logging.Formatter(fmt="%(asctime)s %(name)-12s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        # queue handler
        queue_handler = logging.handlers.QueueHandler(self.event_queue)
        queue_handler.setLevel(logging.DEBUG)
        queue_handler.setFormatter(formatter)
        self.logger.addHandler(queue_handler)

        # file handler
        # file_handler = logging.FileHandler('ui.log', mode='w')
        # file_handler.setLevel(level)
        # file_handler.setFormatter(formatter)
        # self.logger.addHandler(file_handler)


if __name__ == "__main__":
    ui = CommandLineInterface(queue.Queue())
    ui.run()
