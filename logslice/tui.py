"""Terminal UI for interactive log browsing with fuzzy search."""

import curses
from typing import List, Optional
from logslice.log_parser import LogEntry
from logslice.filter_engine import build_filter_chain, apply

LEVEL_COLORS = {
    "error": 1,
    "warn": 2,
    "warning": 2,
    "info": 3,
    "debug": 4,
}


class TUIApp:
    """Interactive curses-based log viewer with live fuzzy filtering."""

    def __init__(self, entries: List[LogEntry]) -> None:
        self.all_entries = entries
        self.filtered: List[LogEntry] = list(entries)
        self.query: str = ""
        self.offset: int = 0
        self.selected: int = 0

    def _filter(self) -> None:
        chain = build_filter_chain(fuzzy=self.query or None)
        self.filtered = apply(self.all_entries, chain)
        self.offset = 0
        self.selected = 0

    def _draw(self, stdscr: "curses.window") -> None:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        list_height = height - 3

        # Header
        header = f" logslice  |  {len(self.filtered)}/{len(self.all_entries)} entries "
        stdscr.addstr(0, 0, header[:width].ljust(width), curses.A_REVERSE)

        # Log lines
        visible = self.filtered[self.offset: self.offset + list_height]
        for idx, entry in enumerate(visible):
            row = idx + 1
            line = str(entry)[:width - 1]
            level = (entry.level or "").lower()
            color_pair = curses.color_pair(LEVEL_COLORS.get(level, 0))
            attr = curses.A_BOLD if idx + self.offset == self.selected else curses.A_NORMAL
            try:
                stdscr.addstr(row, 0, line, color_pair | attr)
            except curses.error:
                pass

        # Search bar
        search_label = f" search: {self.query}"
        stdscr.addstr(height - 2, 0, search_label[:width].ljust(width), curses.A_REVERSE)
        stdscr.addstr(height - 1, 0, " ^C quit  UP/DOWN navigate  ENTER select "[:width], curses.A_DIM)
        stdscr.refresh()

    def run(self, stdscr: "curses.window") -> Optional[LogEntry]:
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_RED, -1)
        curses.init_pair(2, curses.COLOR_YELLOW, -1)
        curses.init_pair(3, curses.COLOR_GREEN, -1)
        curses.init_pair(4, curses.COLOR_CYAN, -1)
        curses.cbreak()
        stdscr.keypad(True)

        while True:
            self._draw(stdscr)
            key = stdscr.getch()

            if key in (curses.KEY_BACKSPACE, 127, 8):
                self.query = self.query[:-1]
                self._filter()
            elif key == curses.KEY_UP:
                if self.selected > 0:
                    self.selected -= 1
                if self.selected < self.offset:
                    self.offset -= 1
            elif key == curses.KEY_DOWN:
                height, _ = stdscr.getmaxyx()
                if self.selected < len(self.filtered) - 1:
                    self.selected += 1
                if self.selected >= self.offset + (height - 3):
                    self.offset += 1
            elif key in (10, 13):  # Enter
                if self.filtered:
                    return self.filtered[self.selected]
            elif key == 3:  # Ctrl+C
                return None
            elif 32 <= key <= 126:
                self.query += chr(key)
                self._filter()


def launch_tui(entries: List[LogEntry]) -> Optional[LogEntry]:
    """Launch the TUI and return the selected entry, or None."""
    app = TUIApp(entries)
    return curses.wrapper(app.run)
