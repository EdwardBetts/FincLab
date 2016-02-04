import curses
from curses import COLOR_WHITE, COLOR_GREEN, COLOR_BLUE, COLOR_CYAN, COLOR_BLACK, COLOR_MAGENTA

from ui.cli_windows import Window, StringWindow, EditorWindow, MenuWindow, MenuTuple
import sys
from itertools import cycle
from time import sleep
from config import config

import queue
import logging
import logging.handlers


# can't rely on curses to find tab, enter, etc.
KEY_TAB = 9

# name some colors (foreground/background pairs) actually defined later through curses.init_pair
BASIC = 0  # not editable
TITLE_ACTIVE = 1
TITLE_INACTIVE = 2
MENU_MESSAGE = 3

logger = logging.getLogger("FincLab.UI")


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
        self.new_updates = False
        self.status = {}  # Holds messages directed to panes other than the pane_output
        self.new_status = False
        self.description = ""  # Holds messages directed to the pane_command
        self.new_description = False
        self.progress = []
        self.new_progress_bar = False

    def write(self, txt):
        self.text = self.text.replace("\n\n", "\n")
        if txt[20:28] == "[Status]":
            # Received some message to indicate the program status
            k, v = txt[28:].split(':')
            self.status[k] = v
            self.new_status = True
        elif txt[20:25] == "[Msg]":
            # Received pure message (exclude logger info)
            self.text += txt[25:]
            self.text = '\n'.join(self.text.split('\n')[-1000:])
            self.new_updates = True
        elif txt[20:26] == "[Desc]":
            # Received strategy description (exclude logger info)
            self.description = txt[26:]
            self.new_description = True
        elif txt[20:30] == "[Progress]":
            # Received two numbers (i.e. 1,100 ) containing progress bar information for 1%
            self.progress = [float(x) for x in txt[30:].split(',')]
            self.new_progress_bar = True
        else:
            self.text += txt
            self.text = '\n'.join(self.text.split('\n')[-1000:])
            self.new_updates = True

    def get_text(self, beg=0, end=-1):
        """
        Return a string. Retrive sepcific rows from the stream.

        Row separater is \n by default.
        """
        self.new_updates = False
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

    def __init__(self, log_queue, config=config):
        """
        Initialise the interface.

        Parameters
        ----------
            log_queue : queue.Queue()
                The event queue for the event-driven system. Log (and message) events will be read from the queue and printed to the User Interface.
        """
        self.log_queue = log_queue
        self.sleep_time = float(config['ui']['refresh_time'])
        self.auto_scale = config.getboolean('ui', 'auto')
        self.stream = StdOutWrapper()
        self.config = config
        self.logger = logging.getLogger("FincLab.UI")

    def start_log_listener(self):
        """ Start the logger listener to take log events from the queue.
        Only starts after initialising the UI.
        """
        # Log listener
        handler = logging.StreamHandler()
        formatter = logging.Formatter(fmt="%(name)-18s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)
        self.listener = logging.handlers.QueueListener(self.log_queue, handler)
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
                if self.stream.new_updates:
                    self.pane_output.clear()
                    output = self.stream.get_last_rows(self.lines_in_output_pane)
                    self.pane_output.refresh_pane(output)
                    self.pane_output.draw_border()
                    self.pane_output.dirty = True
                    self.stream.new_updates = False

                # Refresh app status
                if self.stream.new_status:
                    self.pane_status.clear()
                    # Engine tag
                    if self.stream.status.get("Engine"):
                        self.pane_status._addstr(1, 1, "Engine : {}".format(self.stream.status.get("Engine", 'n/a')))
                    else:
                        self.pane_status._addstr(1, 1, "Countdown: {} secs".format(self.stream.status.get("countdown", 'n/a')))
                    # Components
                    self.pane_status._addstr(3, 1, "Components:")
                    self.pane_status._addstr(4, 1, "-----------")
                    self.pane_status._addstr(5, 1, "  {}".format(self.config['components']['strategy']))
                    self.pane_status._addstr(6, 1, "  {}".format(self.config['components']['data_handler']))
                    self.pane_status._addstr(7, 1, "  {}".format(self.config['components']['execution_handler']))
                    self.pane_status.draw_border()
                    self.pane_status.dirty = True
                    self.stream.new_status = False

                # Refresh strategy description
                if self.stream.new_description:
                    self.pane_command.clear()
                    self.pane_command._addstr(1, 1, self.stream.description)
                    self.pane_command.draw_border()
                    self.pane_command.dirty = True
                    self.stream.new_description = False

                # Refresh progress bar
                if self.stream.new_progress_bar:
                    self.update_progress_bar(0, 100)  # To clear outputs
                    self.update_progress_bar(self.stream.progress[0], self.stream.progress[1])  # To display correct outputs

                # Refresh time
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
            self.start_log_listener()  # start the listener to take log events from the queue (only after the UI has initialised)

            self.logger.debug("Commandline Interface successfully initialised.")
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

    def create_progress_bar(self, value, max_value, bar_length=50):
        # Bar
        if value <= 0:
            percent = float(0)
        else:
            percent = float(value + 1) / max_value
        hashes = '#' * int(round(percent * bar_length))
        spaces = ' ' * (bar_length - len(hashes))

        return ("[{0}] {1:>3}%".format(hashes + spaces, int(round(percent * 100))))

    def update_progress_bar(self, value, max_value):
        """ Update the progress bar which is located at the bottom of the UI

        Parameters
        ----------
            value : float
                the value of the current progress
            max_value : float
                the value when the bar reaches 100%
        """
        # Define progress bar (width of screen is (maxx - 2), height of screen is (maxy -2)
        progress_title = "Progress "
        bar = self.create_progress_bar(value, max_value, self.maxx - len(progress_title) - 4 - 7)  # 4->borders 5->digits at right end of the bar
        self.main_border._addstr(self.maxy - 2, 2, progress_title + bar)
        self.main_border.dirty = True

    def _layout(self):
        """ Core of the Commandline User Interface. Defines the layout of the interface.
        """

        # Manual tiling
        (maxy, maxx) = self.stdscr.getmaxyx()
        (self.maxy, self.maxx) = self.stdscr.getmaxyx()

        if self.auto_scale:
            splitx = int(maxx * .3)
            splity = int(maxy * .7)
        else:
            splitx = 30
            splity = maxy - 13

        # Title height
        title_height = 7

        # initialize windows
        # specify Upper left corner, size, title, color scheme and border/no-border
        self.main_border = StringWindow((0, 0), (maxx, maxy), ' FincLab Ver 0.1 ', TITLE_INACTIVE)
        self.pane_output = StringWindow((splitx, title_height + 1), (maxx - splitx - 1, splity - title_height - 2), 'Output', TITLE_INACTIVE)
        self.pane_menu = MenuWindow((1, title_height + 1), (splitx - 1, splity - title_height - 2), 'Menu', TITLE_INACTIVE)
        self.pane_command = EditorWindow((splitx, splity - 1), (maxx - splitx - 1, maxy - splity - 1), 'Strategy description (or type in commands)', palette=TITLE_INACTIVE, callback=self.pane_output.add_str)
        self.pane_status = Window((1, splity - 1), (splitx - 1, maxy - splity - 1), 'Status', palette=TITLE_INACTIVE)

        self.lines_in_output_pane = splity - title_height - 3

        self.update_progress_bar(0, 100)

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
        queue_handler = logging.handlers.QueueHandler(self.log_queue)
        queue_handler.setLevel(logging.DEBUG)
        queue_handler.setFormatter(formatter)
        self.logger.addHandler(queue_handler)

        # file handler
        # file_handler = logging.FileHandler('ui.log', mode='w')
        # file_handler.setLevel(level)
        # file_handler.setFormatter(formatter)
        # self.logger.addHandler(file_handler)


def start_ui(log_queue, config):
    """ Start the user interface """
    ui = CommandLineInterface(log_queue, config=config)
    ui.run()


if __name__ == "__main__":
    from config import config
    import multiprocessing as mp
    from logger import create_logger
    log_queue = queue.Queue()
    logger = create_logger(log_queue)
    logger.setLevel(logging.DEBUG)

    logger = logging.getLogger("FincLab")
    # Formatter
    formatter = logging.Formatter(fmt="%(asctime)s %(name)-12s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    formatter = logging.Formatter(fmt="%(name)-18s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    # create consoleHandler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # create queue handler for the user interface
    queue_handler = logging.handlers.QueueHandler(log_queue)
    queue_handler.setLevel(logging.DEBUG)
    queue_handler.setFormatter(formatter)
    logger.addHandler(queue_handler)

    # Starts the user interface
    ui_process = mp.Process(target=start_ui, args=(log_queue, config))
    ui_process.start()

    logger.info("yoyoyo")
    logger.info("yoyoyo")
    logger.info("yoyoyo")

