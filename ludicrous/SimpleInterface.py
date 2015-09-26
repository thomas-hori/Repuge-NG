import sys
from consolation.DisplaySelector import DisplaySelector

class SimpleInterface(object):
    """An interface with the user.

    This is double-linked with the object which the user is inhabiting.

    This is in responsible for drawing the level and seeking user input.
    It probably, but doesn't necessarily, uses DisplaySelector to get a
    consolation Display implementation (this is the default behaviour).

    FOV/LOS and panning are absent by default but can be added by
    subclasses."""
    generic_coords = []
    #Semantically public
    def __init__(self, playerobj, use_rpc=False, display=None, debug_dummy=False):
        self.playerobj = playerobj
        self.level = playerobj.level
        if self.level:
            self.level.child_interfaces.append(self)
        self.game = playerobj.game
        #
        if not debug_dummy:
            if display:
                self.display = display
            else:
                self.display = DisplaySelector.get_display(use_rpc)
    def redraw(self):
        #Note: this function may be copyrighted by KSP.
        #To be rewritten.
        """Draw the map (grid and objgrid).

        Presently this, by default, draws grid and (above it) objgrid at once
        and draws the entire grid.

        Unless you are a FOV/LOS engine, you probably don't want to override
        this."""
        if self.playerobj.pt:
            self.display.goto_point(*self.get_viewport_pt())
        colno = 0
        for coordscol, col, col2 in zip(*self.get_viewport_grids()):
            rowno = 0
            for coords, row, row2 in zip(coordscol, col, col2):
                #print rowno, colno, col
                if row2:
                    self.display.plot_tile(colno, rowno, row2[-1].tile)
                elif row:
                    self.display.plot_tile(colno, rowno, row[0])
                rowno += 1
            colno += 1
        self.display.flush_plots()
    def level_rebase(self, newlevel):
        """Link to new level, and bin any cached info about the current level."""
        if self.level != newlevel:
            if self.level:
                self.level.child_interfaces.remove(self)
                assert self not in self.level.child_interfaces
                self.display.push_message("You leave the level.")
                self.level.broadcast("A player has left this level.")
                if len(self.level.child_interfaces) <= 1:
                    self.level.broadcast("This level is now deserted.")
            self.level = newlevel
            if not self.level.child_interfaces:
                self.display.push_message("You arrive on a deserted level.")
            else:
                self.display.push_message("You arrive on an occupied level.")
                self.level.broadcast("A player has arrived.")
                if len(self.level.child_interfaces) == 2:
                    self.level.broadcast("This level is now occupied.")
            self.level.child_interfaces.append(self)
            try:
                self.display.set_window_title(self.level.title_window)
            except NotImplementedError:
                pass
            self.generic_coords = [list(zip(*enumerate(h)))[0] for h in self.level.grid]
            self.generic_coords = [[(x[0], y) for y in x[1]] \
                                   for x in enumerate(self.generic_coords)]
    def flush_fov(self):
        """Bin any cached info about the current level FOV."""
        pass
    def close(self):
        sys.exit()
    def push_message(self, s):
        return self.display.push_message(s)
    def dump_messages(self):
        return self.display.dump_messages()
    def ask_question(self, s):
        return self.display.ask_question(s)
    def slow_ask_question(self, s, p=""):
        return self.display.slow_ask_question(s, p)
    def get_key_event(self):
        return self.display.get_key_event()
    #Semantically protected
    _w = _h = None
    def get_offsets(self):
        """Used for LOS optimisation if only part of map visible."""
        self._w, self._h = width, height = self.display.get_dimensions()
        if width < 0:
            width = 80
        if height < 0:
            height = 23
        width -= 1
        height -= 4
        offsetx = 0
        roffsetx = width
        offsety = 0
        roffsety = height
        return width, height, offsetx, offsety, roffsetx, roffsety
    def get_viewport_grids(self):
        return self.generic_coords, self.level.grid, self.level.objgrid
    def get_viewport_pt(self):
        return self.playerobj.pt