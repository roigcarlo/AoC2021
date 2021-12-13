import curses

def main(stdscr):
    curses.start_color()
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i + 1, i, -1)
    try:
        for i in range(0, 36):
            for j in range(0, 6):
                stdscr.addstr(str('X'), curses.color_pair(17+i*6+j))
            stdscr.addstr("\n", curses.color_pair(i))
    except curses.ERR:
        # End of screen reached
        pass
    stdscr.getch()

curses.wrapper(main)