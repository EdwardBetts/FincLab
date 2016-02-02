import curses
from curses import COLOR_WHITE, COLOR_GREEN, COLOR_BLUE, COLOR_CYAN, \
    COLOR_BLACK, COLOR_MAGENTA

from ui.cli_windows import StringWindow, EditorWindow, \
    MenuWindow, MenuTuple

from itertools import cycle

from random import randint
from time import time, sleep
import queue

# can't rely on curses to find tab, enter, etc.
KEY_TAB = 9

# name some colors (foreground/background pairs) actually defined later through curses.init_pair
BASIC = 0  # not editable
TITLE_ACTIVE = 1
TITLE_INACTIVE = 2
MENU_MESSAGE = 3


class OutputWindow(StringWindow):
    '''String Window that just spews out some words at random times'''

    def __init__(self, *args, **kwargs):
        super(OutputWindow, self).__init__(*args, **kwargs)
        self.next_time = time() + randint(1, 4)
        self.things_to_say = self.fake_chat_gen()

    def fake_chat_gen(self):
        intro = [
            'This is a fake chat program',
            'Press TAB to switch between windows',
            'When you type in the editor, this window is still responsive',
            'I could be getting information from a socket rather than a dumb loop!',
            'Press CTRL+C to quit.',
            'So, uh, have fun and all.',
        ]

        annoying = cycle(['this is the song that never ends',
                          'It goes on and on my FRIEND!',
                          'Some people started singing it not knowing what it was.',
                          'and then they kept on singing it for-ever just because'])

        for s in intro:
            yield s
        for s in annoying:
            yield s

    def update(self):
        now = time()
        if now > self.next_time:
            self.next_time = now + randint(1, 5)
            self.add_str(next(self.things_to_say), palette=BASIC)
        super(OutputWindow, self).update()


def run(stdscr, event_queue):
    """ Core of the Commandline User Interface.

    Parameters
    ----------
        stdscr : the standard screen of the curses
        event_queue : queue.Queue()
            Queue object to read messages from
    """

    # Manual tiling
    (maxy, maxx) = stdscr.getmaxyx()
    splitx = int(maxx * .3)
    splity = int(maxy * .7)

    # Title height
    title_height = 7

    # initialize windows
    # specify Upper left corner, size, title, color scheme and border/no-border

    main_border = StringWindow((0, 0), (maxx, maxy), ' FincLab Ver 0.1 ', TITLE_INACTIVE)
    pane_output = OutputWindow((splitx, title_height + 1), (maxx - splitx - 1, splity - title_height - 1), 'Output', TITLE_INACTIVE)
    pane_menu = MenuWindow((1, title_height + 1), (splitx - 1, splity - title_height - 1), 'Menu', TITLE_INACTIVE)
    pane_command = EditorWindow((splitx, splity), (maxx - splitx - 1, maxy - splity - 1), 'Type Commands...', palette=TITLE_INACTIVE, callback=pane_output.add_str)
    pane_status = StringWindow((1, splity), (splitx - 1, maxy - splity - 1), 'Status', palette=TITLE_INACTIVE)

    # Set menu options with corrisponding callbacks
    menu_actions = [
        MenuTuple("Say 'Hi'", (pane_output.add_str, 'Hello from the Menu', MENU_MESSAGE)),
        MenuTuple('Say something else', (pane_output.add_str, 'From the Menu, Hello!', MENU_MESSAGE)),
        MenuTuple('I Prefer Cyan', (curses.init_pair, TITLE_INACTIVE, COLOR_CYAN, COLOR_BLACK)),
        MenuTuple('I Prefer Green', (curses.init_pair, TITLE_INACTIVE, COLOR_GREEN, COLOR_BLACK)),
        MenuTuple('I Prefer Plain', (curses.init_pair, TITLE_INACTIVE, COLOR_WHITE, COLOR_BLACK))]
    pane_menu.set_menu(menu_actions)

    # Put all the windows in a list so they can be updated together
    windows = [main_border, pane_output, pane_menu, pane_command, pane_status]

    # create input window cycling an input window must have a process_key(key) method
    input_windows = cycle([pane_menu, pane_command])
    active_window = next(input_windows)
    active_window.draw_border(TITLE_ACTIVE)

    # Add titles and other texts
    main_border.add_str("  FincLab Event-Driven Live-Trading / Backtesting Engine")
    main_border.add_str(" ")
    main_border.add_str("  Author: Peter Lee (mr.peter.lee@hotmail.com)")
    main_border.add_str("  Instrctions:")
    main_border.add_str('      - Please configure program settings in the "config.ini"')
    main_border.add_str("      - End-of-day data will be downloaded automatically if not found.")
    pane_status.add_str("Press <TAB> to switch pane")
    pane_status.add_str("[Engine status]: Backtesting")

    # Main Program loop.  CTRL+C to break it.
    while True:
        # asynchronously try to get the key the user pressed
        key = stdscr.getch()
        if key == curses.ERR:
            # no key was pressed.  Do house-keeping
            dirtied = 0
            for win in windows:
                dirtied += win.dirty
                win.update()
            # if dirtied:
            stdscr.refresh()

            sleep(.1)  # Refresh rate = 10 times per second

        elif key == KEY_TAB:
            # cycle input window
            active_window.draw_border()  # uses window default
            active_window = next(input_windows)
            active_window.draw_border(TITLE_ACTIVE)
        else:
            # every other key gets processed by the active input window
            active_window.process_key(key)


def launch_cli(event_queue):
    """ Launch the curses user interface

    Parameters
    ----------
        event_queue : queue.Queue()
            The event queue for the event-driven system. Log (and message) events will be read from the queue and printed to the User Interface."""
    # Set up screen.  Try/except to make sure the terminal gets put back together no matter what happens
    try:
        # https://docs.python.org/2/howto/curses.html
        stdscr = curses.initscr()
        curses.start_color()
        curses.noecho()  # let input windows handle drawing characters to the screen
        curses.cbreak()  # enable key press asynch
        stdscr.nodelay(1)  # enable immediate time out (don't wait for keys at all)
        stdscr.keypad(1)  # enable enter, tab, and other keys

        # Set initial palette
        curses.init_pair(TITLE_ACTIVE, COLOR_BLUE, COLOR_BLACK)
        curses.init_pair(TITLE_INACTIVE, COLOR_WHITE, COLOR_BLACK)
        curses.init_pair(MENU_MESSAGE, COLOR_MAGENTA, COLOR_BLACK)

        # run while wrapped in this try/except
        run(stdscr, event_queue)

    except Exception:
        # put the terminal back in it's normal mode before raising the error

        curses.nocbreak()
        stdscr.keypad(0)
        curses.echo()
        curses.endwin()
        raise
    finally:
        curses.nocbreak()
        stdscr.keypad(0)
        curses.echo()
        curses.endwin()
        print('This terminal can%s display color'.format(["'t", ''][curses.has_colors()]))

if __name__ == "__main__":
    launch_cli(queue.Queue())
