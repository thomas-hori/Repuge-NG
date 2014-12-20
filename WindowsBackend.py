import sys
from ConsoleBackend import ConsoleBackend
from WindowsTiles import WindowsTiles
from compat3k import *

class WindowsBackend(ConsoleBackend):
    """Partially implementing base class"""
    _tiles_class=WindowsTiles
    def goto_point(self,x,y):
        self.point[:]=x,y
        self._conio_gotoxy(x,y)
    def set_window_title(self,title):
        self._conio_settitle(bytes(title))
    def get_key_event(self):
        self.dump_messages()
        return self._conio_getkey()
    def _plot_character(self,x,y,c):
        self._conio_puttext(y,x,y,x,bytes(c+"\x07"))