# Random Dungeon - use TKInter to draw
from tkinter import *
import random


class Cell:
    def __init__( self, pos = None ):
        self.pos = pos
        self.connection = {}
    def is_connected( self ):
        return len( self.connection ) > 0


def shift_position( pos, offset, scale = (1,1) ):
    (x,y) = pos
    (ox,oy) = offset
    (sx,sy) = (scale,scale) if type(scale) != type(()) else scale
    return (x+ox*sx),(y+oy*sy)


class CellExits:
    def __init__( self, offsets, side = 0 ):
        if ( len(offsets) % 2 ) != 0:
            raise IndexError
        self.side = side
        self.offsets = offsets
        self.side_count = len( self.offsets )
    def __len__( self ):
        return self.side_count
    def set( self, side ):
        self.side = side%self.side_count
    def next( self ):
        self.set( self.side + 1 )
    def offset( self ):
        return self.offsets[self.side]
    def back_offset( self ):
        back_offset = (self.side + self.side_count//2)%self.side_count
        return self.offsets[back_offset]


class CellMaze:
    def __init__( self, side_x, side_y, cell_exits ):
        self.side_x = side_x
        self.side_y = side_y
        self.cell_exits = cell_exits
        self.cell_array = {}
    def cell( self, pos ):
        if self.in_bounds(pos):
            return self.cell_array[pos]
        return None
    def __len__( self ):
        return len( self.cell_array )
    def cells( self ):
        for cell in self.cell_array.values():
            yield cell
    def in_bounds( self, pos ):
        return pos in self.cell_array
    def random_position( self, connected = True ):
        while True:
            rx = random.randrange( self.side_x )
            ry = random.randrange( self.side_y )
            rpos = (rx,ry)
            cell = self.cell( rpos )
            if self.in_bounds( rpos ) and ( cell.is_connected() == connected ):
                 break
        return rpos
    def set_random_direction( self ):
        rd = random.randrange( len(self.cell_exits) )
        self.cell_exits.set( rd )
    def try_direction( self, pos ):
        offset = self.cell_exits.offset()
        newpos = shift_position( pos, offset )
        if self.in_bounds( newpos ):
            if not self.cell_array[newpos].is_connected():
                backoffset = self.cell_exits.back_offset()
                self.cell_array[pos].connection[ offset ] = newpos
                self.cell_array[newpos].connection[ backoffset ] = pos
                return newpos
        return None
    def pick_neighbour( self, pos ):
        self.set_random_direction()
        for tries in range( len( self.cell_exits ) ):
            newpos = self.try_direction( pos )
            if newpos:
                return newpos
            self.cell_exits.next()
        return None


def create_rectangular_maze( side_x, side_y ):
    offsets = [ (0,-1), (1,0), (0,1), (-1,0) ]
                 
    cell_exits = CellExits( offsets )
    maze = CellMaze( side_x, side_y, cell_exits )

    for y in range( side_y ):
        for x in range( side_x ):
            pos = (x,y)
            maze.cell_array[pos] = Cell( pos )
    return maze


def create_maze( side_x, side_y, shape_generator ):
    target_fill_percent = 80
    maze = shape_generator( side_x, side_y )
                 
    #pick random start cell
    startpos = rpos = maze.random_position( False )
    connected = 1

    done = False
    while not(done):
        newpos = maze.pick_neighbour( rpos )
        if newpos:
            rpos = newpos
            connected += 1
        else:
            #see what percent filled
            pcf = 100*connected/len(maze)
            if pcf >= target_fill_percent:
                done = True
            else:
                rpos = maze.random_position( True )
    return maze,startpos,rpos


class Rect:
    def __init__( self, l, t, r = None, b = None ):
        if r is None:
            self.rect = ( l[0], l[1], t[0], t[1] )
        else:
            self.rect = ( l, t, r, b )
    def mid_point( self ):
        ( l, t, r, b ) = self.rect
        return ( l + r )/2,( t + b )/2
    def top_left( self ):
        return self.rect[0],self.rect[1]
    def bottom_right( self ):
        return self.rect[2],self.rect[3]
        

class GameBoard:
    BORDER = 10
    LINE_HEIGHT = 30
    CELL_SIZE = 50
    CELL_BORDER = 5
    STATUS_LINES = 3
    def __init__( self, cellx, celly ):
        self.master = Tk()
        grid_w = cellx*self.CELL_SIZE
        grid_h = celly*self.CELL_SIZE
        width = 2*self.BORDER+grid_w
        status_start = 2*self.BORDER+grid_h
        status_height = self.STATUS_LINES*self.LINE_HEIGHT
        #
        self.grid_area = Rect(self.BORDER,self.BORDER,self.BORDER+grid_w,self.BORDER+grid_h)
        self.status_area = Rect(self.BORDER,status_start,self.BORDER+grid_w,status_start+status_height)
        self.canvas = Canvas( self.master, width=width,
                              height = self.BORDER+status_start+status_height )
        self.canvas.pack()
    def run( self ):
        self.master.mainloop()
    def status_text( self, line, text ):
        xy = shift_position( self.status_area.top_left(), (0,line*self.LINE_HEIGHT) )
        self.canvas.create_text( xy, text = text, anchor = W )
    def draw_connections( self, cell, rect ):
        start = rect.mid_point()
        #draw connections
        for direction in cell.connection:
            end = shift_position( start, direction, self.CELL_SIZE )
            self.canvas.create_line( start, end, width = 5 )
    def draw_cell_labels( self, cell, text, rect ):
        if cell.is_connected():
            start = shift_position( rect.top_left(), (1,1), self.CELL_BORDER )
            end = shift_position( rect.bottom_right(), (1,1), -self.CELL_BORDER )
            self.canvas.create_rectangle( start, end, fill="yellow", outline="red" )
        self.canvas.create_text( rect.mid_point(), text=text )
    def draw_cells( self, maze ):
        origin = self.grid_area.top_left()
        for cell in maze.cells():
            x,y = cell.pos
            xy0 = shift_position( origin, (x,y), self.CELL_SIZE )
            xy1 = shift_position( xy0, (1,1), self.CELL_SIZE )
            self.canvas.create_rectangle( xy0, xy1 )
            self.draw_connections( cell, Rect(xy0, xy1) )
        for cell in maze.cells():
            x,y = cell.pos
            xy0 = shift_position( origin, (x,y), self.CELL_SIZE )
            xy1 = shift_position( xy0, (1,1), self.CELL_SIZE )
            self.draw_cell_labels( cell, str(cell.pos), Rect(xy0, xy1) )


#main program
def main():
    random.seed()
    cellsX = 10
    cellsY = 10
    maze,startpos,endpos = create_maze( cellsX, cellsY, create_rectangular_maze )
    g = GameBoard( cellsX, cellsY )
    g.draw_cells( maze )
    g.status_text( 1, 'Start cell: ' + str(startpos) )
    g.status_text( 2, 'End cell: '+str(endpos) )
    g.run()

if __name__ == "__main__":
    main()
    
