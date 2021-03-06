from ludicrous.SimpleInterface import SimpleInterface
import math

__copying__="""
Written by Thomas Hori

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/."""

halfpi = math.pi//2

class DumbLosInterface(SimpleInterface):
    """Dumb line of site.  An interface class which adds field of view support.

    Slow.
    """
    _los_cache = None
    _fov_cache = None
    fov_status = 1
    def _transparent(self, cell):
        return cell[0].startswith("floor") or cell[0].endswith("_open")
    def _fov_check(self, x, y, passthrough_once=True):
        if (not self.fov_status) or (self.game.debug_fov_off):
            return True, "ind"
        if not hasattr(self, "playerobj") or self.playerobj == None or self.playerobj.pt == None:
            return True, "ind"
        if ((x, y) in self._los_cache) and not passthrough_once:
            #Apparently (x, y) can still not be in it even after
            #the first conditional.  What the skanking heck?
            if (x, y) in self._los_cache:
                return self._los_cache[(x, y)], "nul"
        if (x < 0) or (y < 0) or (x >= len(self.level.grid)) or (y >= len(self.level.grid[0])):
            return False, "nul"

        junk, junk2, offsetx, offsety, roffsetx, roffsety = self.get_offsets()
        #Normal elif/else doesn't really work here
        ret = -1
        typ = "ind"
        if ret == -1 and (self.playerobj.pt in self._fov_cache) \
           and ((x, y) in self._fov_cache[self.playerobj.pt]) and not passthrough_once:
            ret = True
            typ = "nul"
        if ret == -1 and x < offsetx or x > roffsetx:
            #Off the viewport
            ret = False
        if ret == -1 and y < offsety or y > roffsety:
            #Off the viewport
            ret = False
        if ret == -1 and x == self.playerobj.pt[0] and y == self.playerobj.pt[1]:
            #Trace has reached the destination successfully
            ret = True
            typ = "nul"
        if ret == -1 and self.level.grid[x][y] and \
           (not self._transparent(self.level.grid[x][y])) and not passthrough_once:
            #Blocking object has been encountered
            ret = False
        if ret == -1: #i.e. if below 'if's will be executed
            ycomp = abs(y-self.playerobj.pt[1])
            xcomp = abs(x-self.playerobj.pt[0])
        if ret == -1 and passthrough_once and self.level.grid[x][y] \
           and (not self._transparent(self.level.grid[x][y])):
            #From a wall: the actual path to the player obviously includes the floor, not more wall.
            if ret == -1 and ycomp > 0:
                n = self.level.grid[x][y-int((y-self.playerobj.pt[1])/abs(y-self.playerobj.pt[1]))]
                if n and n[0].startswith("floor"):
                    ret, typ = self._fov_check(x, y-int((y-self.playerobj.pt[1]) \
                                                        /abs(y-self.playerobj.pt[1])), False)
            if ret == -1 and ycomp < xcomp:
                n = self.level.grid[x-int((x-self.playerobj.pt[0])/abs(x-self.playerobj.pt[0]))][y]
                if n and n[0].startswith("floor"):
                    ret, typ = self._fov_check(x-int((x-self.playerobj.pt[0]) \
                                                     /abs(x-self.playerobj.pt[0])), y, False)
            if ret == -1 and ycomp > 0 and ycomp < xcomp:
                n = self.level.grid[x-int((x-self.playerobj.pt[0])/abs(x-self.playerobj.pt[0]))] \
                                   [y-int((y-self.playerobj.pt[1])/abs(y-self.playerobj.pt[1]))]
                if n and n[0].startswith("floor"):
                    ret, typ = self._fov_check(x-int((x-self.playerobj.pt[0]) \
                                                     /abs(x-self.playerobj.pt[0])),
                                               y-int((y-self.playerobj.pt[1]) \
                                                     /abs(y-self.playerobj.pt[1])), False)
        if ret == -1 and ycomp >= (3.73*xcomp): #tan of 75deg
            #Vertical is closest approximation for now
            ret, typ = self._fov_check(x, y-int((y-self.playerobj.pt[1]) \
                                                /abs(y-self.playerobj.pt[1])), False)
        if ret == -1 and ycomp >= (0.27*xcomp): #tan of 15deg
            #45deg is closest approximation for now
            ret, typ = self._fov_check(x-int((x-self.playerobj.pt[0]) \
                                             /abs(x-self.playerobj.pt[0])),
                                       y-int((y-self.playerobj.pt[1])
                                             /abs(y-self.playerobj.pt[1])), False)
        if ret == -1:
            #Horizontal is closest approximation for now
            ret, typ = self._fov_check(x-int((x-self.playerobj.pt[0]) \
                                             /abs(x-self.playerobj.pt[0])), y, False)

        if typ == "nul" and x != self.playerobj.pt[0]:
            typ = (x, y)
        if typ == "nul" and y != self.playerobj.pt[1]:
            typ = (x, y)
        if not passthrough_once:
            self._los_cache[(x, y)] = ret
            if ret:
                if typ not in self._fov_cache:
                    self._fov_cache[typ] = []
                if self.playerobj.pt not in self._fov_cache:
                    self._fov_cache[self.playerobj.pt] = []
                self._fov_cache[typ].append((x, y))
                self._fov_cache[self.playerobj.pt].append((x, y))
        return ret, typ
    def redraw(self):
        #Note: this function is old.
        """Draw the map (grid and objgrid)."""
        if self.playerobj.pt:
            self.display.goto_point(*self.get_viewport_pt())
        if not self.generic_coords:
            #I.E. repossessed from a save.
            self.regen_generic_coords()
        colno = 0
        self._los_cache = {}
        if not self._fov_cache:
            self._fov_cache = {}
        for coordscol, col, col2 in zip(*self.get_viewport_grids()):
            rowno = 0
            for coords, row, row2 in zip(coordscol, col, col2):
                row2 = self.sort_ostack(row2)
                #print colno, rowno, col
                if self._fov_check(*coords)[0]:
                    if row2:
                        self.display.plot_tile(colno, rowno, row2[-1].tile)
                    elif row:
                        self.display.plot_tile(colno, rowno, row[0])
                else:
                    self.display.plot_tile(colno, rowno, "space")
                rowno += 1
            colno += 1
        self.display.flush_plots()
    def flush_fov(self):
        """Bin any cached info about the current level FOV."""
        self._fov_cache = {}
        self.level.redraw()
    def level_rebase(self, newlevel):
        """Link to new level, and bin any cached info about the current level."""
        if self.level != newlevel:
            SimpleInterface.level_rebase(self, newlevel)
            self._los_cache = {}
            self._fov_cache = {}
            self.level.redraw()
