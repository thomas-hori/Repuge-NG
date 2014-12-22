import time
from BackendSelector import BackendSelector
#n.b. put shadowtracer, when introduced, elsewhere (mixin?).

class Level(object):
    """Base class of a level.
    
    Notable attributes and methods:
    - run() - normally the level entrypoint.  Takes no args but self.
    - grid - list of lists of type-tuples for main level.
      A type-tuple is a tuple (type, extra_data) where extra_data is
      data internally used by the level code r.e. the status and 
      identity of the feature.  (Whereas type is just the tile type).
    - objgrid - like grid, but for objects placed upon the map rather
      than constituting part of it, e.g. a collectable.
    
    To do:
    - The objgrid system really needs to be deprecated with the user
      kept track of as with other single objects, and with multiple 
      objects per square.  So a list of objects with their coords?
      Or a set???
    """
    def __init__(self):
        """Initialise the instance (this will run upon creation).
        
        By default: obtain a backend, initialise the grids, draw the 
        map and execute the run() method.
        
        Could be overriden by subclasses, but do remember to obtain a 
        self.backend by some means before trying to output anything.
        More recommended is to override run() and/or readmap().
        """
        self.backend=BackendSelector.get_backend()
        self.readmap()
        self.redraw()
        self.run()
    def _gengrid(self,x,y):
        grid=[]
        for i in range(x):
            file=[] #row (x), file (y), stack (z)
            for j in range(x):
                file.append([])
            grid.append(file)
        return grid
    def readmap(self):
        """Creates self.grid and self.objgrid.
        
        Default behaviour generates self.grid from coded grid format
        and self.objgrid is generated empty.
        
        Coded grid format:
        
        - self.list_of_symbols is set to a character-to-tilename 
          mapping, maximum width 50 tiles, maximum height 19 tiles.
        - self.coded_grid is set to a multi-line string coding the map 
          using these symbols.
        
        The code characters used are included in the grid as extra data.
        So multiple internally different e.g. vfeature can be coded with 
        different characters and detected as different by the level code.
        
        This default behaviour may be overridden by subclasses.  General
        idea is that self.grid and self.objgrid are initialised."""
        #Width 50 not 80 as 16x16 tiles are a conceivable backend and
        #my monitor's max res is 1024x768
        #Height 19 as this is the maximum height to avoid lxterminal 
        #scrolling (thus shifting the viewport aaaargggggghhhh)
        self.grid=self._gengrid(50,19)
        self.objgrid=self._gengrid(50,19)
        rowno=0
        for row in self.coded_grid.split("\n"):
            colno=0
            for col in row:
                self.grid[colno][rowno]=self.list_of_symbols[col],col
                colno+=1
            while len(row)<50:
                self.grid[len(row)][rowno]=("space"," ")
                row+=" "
            rowno+=1
        ##I forget the point of this.
        ##In any case, with the new standardisation measures on what is 
        ##x and what is y, it cuts a swathe through the display and model.
        ##So no.
        #for i in range(19-len(self.coded_grid.split("\n"))):
        #    self.grid[18-i]=[("space","")]*50
    def redraw(self):
        """Draw the map (grid and objgrid).
        
        Presently this, by default, draws grid and (above it) objgrid at once
        and draws the entire grid without attempting to trace visibility.  It
        is therefore equivalent to the drawmap2(...) from older versions of the
        previous generation, or to drawmap(...) with the shadowtracer disabled
        in later versions of the previous generation.  It is based on the 
        former as I intend to discard the illegible mess which is the latter 
        code and rewrite the shadowtracer from scratch.
        
        drawmap(...) / drawmap2(...) was invoked through redraw() which, by 
        means of pseudo-closures, passed in the relevant grids.  With this new
        OOP generation, the latter is now redundant.  Hence drawmap() has now 
        been merged into redraw().
        
        Unless you are a shadowtracer, you probably don't want to override 
        this."""
        colno=0
        for col,col2 in zip(self.grid,self.objgrid):
            rowno=0
            for row,row2 in zip(col,col2):
                #print rowno,colno,col
                if row2:
                    self.backend.plot_tile(colno,rowno,row2[0])
                elif row:
                    self.backend.plot_tile(colno,rowno,row[0])
                rowno+=1
            colno+=1
    #
    def get_index_grid(self,x,y):
        return self.grid[x][y]
    def get_index_objgrid(self,x,y):
        return self.objgrid[x][y]
    def set_index_grid(self,v,x,y):
        self.grid[x][y]=v
    def set_index_objgrid(self,v,x,y):
        self.objgrid[x][y]=v
    #
    def followline_user(self,delay,points):
        """Move the user visibly down a list of points."""
        import time
        for i in points[:-1]:
            self.set_index_objgrid(("user",None),*i)
            pt=i[::-1]
            self.backend.goto_point(*pt)
            self.redraw()
            time.sleep(delay)
            self.set_index_objgrid((),*i)
        i=points[-1]
        self.set_index_objgrid(("user",None),*i)
        pt=i[::-1]
        self.backend.goto_point(*pt)
        self.redraw()
        return pt
    def followline(self,delay,points,typeo):
        """Move a non-user object visibly down a list of points.
        (typeo should be the type tuple of the object)."""
        import time
        for i in points[:-1]:
            self.set_index_objgrid(typeo,*i)
            self.redraw()
            time.sleep(delay)
            self.set_index_objgrid((),*i)
        self.set_index_objgrid(typeo,*points[-1])
        self.redraw()
    def move_user(self,pt1,pt2):
        """Move the user from pt1 to pt2.
        
        XXX location should be kept track of by the class!
        """
        self.set_index_objgrid((),*pt1)
        self.set_index_objgrid(("user",None),*pt2)
        self.backend.goto_point(*pt2)
        self.redraw()
    #
    def run(self):
        """Standard level entry point.  Should be overriden by subclass."""
        raise NotImplementedError("should be implemented by level subclass")
    #