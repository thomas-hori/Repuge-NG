import time
#The "threading" module over-complicates things imo
try:
    from thread import start_new_thread #pylint: disable = import-error
except ImportError:
    #3k
    from _thread import start_new_thread #pylint: disable = import-error

from ludicrous.Saving import Saving

__copying__="""
Written by Thomas Hori

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/."""

class Level(object):
    """Base class of a level.
    """
    WIDTH = 100
    HEIGHT = 100
    starting_pt = (0, 0)
    coded_grid = None
    list_of_symbols = None
    use_dm = False
    #
    game = None
    grid = None
    objgrid = None
    child_objects = None
    child_interfaces = None
    dm_grid = None
    dm_grid2 = None
    #
    def __init__(self, game, restore=None):
        if restore:
            self.__dict__.update(restore)
            self.child_interfaces = []
            for obj in self.child_objects:
                obj.level = self
            start_new_thread(self.run, ())
            return
        self.game = game
        self.child_objects = []
        self.child_interfaces = []
        self.initmap()
        self.initialise()
        start_new_thread(self.run, ())
    def __reduce__(self):
        """Implementation of the Pickle protocol."""
        return (self.__class__, (None, Saving.strip_methods(self.__dict__,("game","child_interfaces"))))
    __safe_for_unpickling__=True
    def reown(self, game):
        """Restore cyclic references to the game after loading a save."""
        self.game = game
        for obj in self.child_objects:
            obj.game = game
        for obj in self.child_interfaces:
            obj.game = game
    def bring_to_front(self, playerobj, whence="unspecified"): #pylint: disable = unused-argument
        """To be called to make this level the active level for a
        player, which may be anything from immediately after creation
        to never.

        The general idea is to take control of the player object, by
        placing it on the level via its place(...) method.  The
        mechanics of GridObject will then take care of hooking up
        that player's interface.

        The whence argument specifies how the level was entered.
        Typically expected values are:

        - "starting"
        - "advancement"
        - "regression"
        - "restoring"
        - "jumping"
        - "unspecified"

        but a Game subclass may pass any object imaginable.  It is
        paramount that those levels which process this are
        compatible with the Game subclass with which they are used.
        """
        if whence!="restoring":
            playerobj.place(self.starting_pt[0], self.starting_pt[1], self)
        else:
            playerobj.place(playerobj.pt[0], playerobj.pt[1], self)
    def _gengrid(self, x, y):
        #Note: this function is old.
        grid = []
        for i in range(x):  #pylint: disable = unused-variable
            file_ = [] #row (x), file (y), stack (z)
            for j in range(y):  #pylint: disable = unused-variable
                file_.append([])
            grid.append(file_)
        return grid
    def readmap(self):
        #Note: this function is old.
        """Generates self.grid from coded grid format.

        Whereas self.objgrid is generated empty.

        Coded grid format:

        - self.list_of_symbols is set to a character-to-tilename
          mapping, maximum width 50 tiles, maximum height 19 tiles.
        - self.coded_grid is set to a multi-line string coding the map
          using these symbols.

        The code characters used are included in the grid as extra data.
        So multiple internally different e.g. vfeature can be coded with
        different characters and detected as different by the level code."""
        if self.HEIGHT==type(self).HEIGHT: #Definitely must be newstyle class for this
            self.HEIGHT=len(self.coded_grid.split("\n"))
            _w = 0
            for row in self.coded_grid.split("\n"):
                if len(row) > _w:
                    _w = len(row)
            self.WIDTH=_w
        self.grid = self._gengrid(self.WIDTH, self.HEIGHT)
        self.objgrid = self._gengrid(self.WIDTH, self.HEIGHT)
        rowno = 0
        for row in self.coded_grid.split("\n"):
            colno = 0
            for col in row:
                self.grid[colno][rowno] = self.list_of_symbols[col], col
                colno += 1
            while len(row) < self.WIDTH:
                self.grid[len(row)][rowno] = ("space", " ")
                row += " "
            rowno += 1
    def initmap(self):
        """Creates self.grid and self.objgrid.

        By default, calls readmap().

        This default behaviour may be overridden by subclasses.  General
        idea is that self.grid and self.objgrid are initialised."""
        self.readmap()
    #
    def initialise(self):
        """Ran after playerobj placed.  To be overridden by subclasses."""
        pass
    #
    def redraw(self):
        for aninterface in self.child_interfaces:
            aninterface.redraw()
    def broadcast(self, m):
        for i in self.child_interfaces:
            i.push_message(m)
    def run(self):
        while 1:
            if self.game!=None:
                self.gen_dijkstra_map()
                #Each creature gets a move:
                for obj in self.child_objects[:]:
                    while self.game.loading_lock:
                        time.sleep(0.2)
                    obj.tick()
                #Avoid inactive levels tightlooping and throttling
                #the system:
                if not self.child_objects:
                    time.sleep(0.6)
            else:
                time.sleep(0.6)
    #
    def get_index_grid(self, x, y):
        return self.grid[x][y]
    def set_index_grid(self, v, x, y):
        self.grid[x][y] = v
    #
    def handle_move(self, dest, playerobj): #pylint: disable = unused-argument
        """Handle a move command by the user. --> True to go ahead or False
        to block the move.

        Default allows no movement.  May be overridden by level subclass."""
        return 0
    #
    def handle_command(self, key_event, playerobj): #pylint: disable = unused-argument
        r"""Handle a command by the user.  This is not called on move
        commands by default.

        Default does nothing.  May be overridden by level subclass.

        BE AWARE THAT the same key may sent a different event on different
        platforms/backends.  This much is not rigidly standardised between
        backends.  Play safe: test key_event.lower() against ("return",
        "enter", "\r", "\n", "\r\n") for example."""
        return 0
    #
    def grid_dimens(self):
        width = len(self.grid)
        height = 0
        for col in self.grid:
            if len(col) > height:
                height = len(col)
        return width, height
    def gen_dijkstra_map(self):
        """Calculate shortest distance to the nearest player for each grid cell.
        Called a Dijkstra map, despite not really being Dijkstra's Algorithm I 
        don't think.

        If self.use_dm == False, do nothing.

        Monsters should use dm_grid for pursuing the player.

        If dm_grid on a neighbouring cell equals dm_grid2 on that cell, then the
        player is visible."""
        if not self.use_dm:
            return
        _w, _h = self.grid_dimens()
        self.dm_grid = [list(i) for i in ([65534]*_h, )*_w]
        self.dm_grid2 = [list(i) for i in ([65534]*_h, )*_w]
        for i in self.child_interfaces:
            if hasattr(i, "playerobj") and hasattr(i.playerobj, "pt") and i.playerobj.pt:
                _x, _y = i.playerobj.pt
                self.dm_grid[_x][_y] = 0
                self.dm_grid2[_x][_y] = 0
        changed = 1
        _r = range(_w)
        while changed == 1:
            changed = 0
            for x in _r:
                h = len(self.grid[x])
                for y in range(h):
                    adjacents = ([(x-1, y-1)] if x > 0 and y > 0 else []) \
                              + ([(x, y-1)] if y > 0 else []) \
                              + ([(x+1, y-1)] if x < (_w-1) and y > 0 else []) \
                              + ([(x+1, y)] if x < (_w-1) else []) \
                              + ([(x+1, y+1)] if x < (_w-1) and y < (h-1) else []) \
                              + ([(x, y+1)] if y < (h-1) else []) \
                              + ([(x-1, y+1)] if x > 0 and y < (h-1) else []) \
                              + ([(x-1, y)] if x > 0 else [])
                    for _x, _y in adjacents:
                        if self.grid[x][y][0].endswith("_open") \
                           or self.grid[x][y][0].startswith("floor"):
                            possible = self.dm_grid[_x][_y]+1
                            if possible < self.dm_grid[x][y]:
                                changed = 1
                                self.dm_grid[x][y] = possible
                        possible = self.dm_grid2[_x][_y]+1
                        if possible < self.dm_grid2[x][y]:
                            changed = 1
                            self.dm_grid2[x][y] = possible
