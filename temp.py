# Curses tutorial
#
import curses
stdscr = curses.initscr()

curses.noecho()  # turnoff automatic echoing of keys to the screen
curses.cbreak()  # do not need ENTER to be pressed

stdscr.keypad(True)  # enable special keys such as Page up

# Terminal the curses
curses.nocbreak()
stdscr.keypad(False)
curses.echo()
curses.endwin()


def main(stdscr):
    # Clear screen
    stdscr.clear()

    stdscr.addstr("oh yoyo")
    # This raises ZeroDivisionError when i == 10.
    for i in range(0, 11):
        v = i - 10
        stdscr.addstr(i, 0, '10 times by {} is {}'.format(v, 10 * v),
                      curses.A_BOLD)

    stdscr.refresh()
    stdscr.getkey()

if __name__ == '__main__':
    curses.wrapper(main)
