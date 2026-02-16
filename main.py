import tkinter as tk
import time
from collections import deque

# Grid size
ROWS = 10
COLS = 10
CELL_SIZE = 40  # pixels

# Colors
EMPTY_COLOR = "lightgrey"
WALL_COLOR = "black"
START_COLOR = "green"
TARGET_COLOR = "red"
FRONTIER_COLOR = "yellow"
EXPLORED_COLOR = "lightblue"
PATH_COLOR = "purple"

# Sample static grid (0 = empty, 1 = wall)
grid = [
    [0,0,0,0,0,0,0,0,0,0],
    [0,0,1,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,1,0],
    [0,1,0,0,0,0,1,0,0,0],
    [0,0,0,0,0,0,0,0,1,0],
    [0,0,1,0,0,0,0,1,0,0],
    [0,0,0,0,1,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,1,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0]
]

START = (0, 0)
TARGET = (9, 9)

def draw_grid(canvas):
    canvas.delete("all")  # Clear canvas
    for row in range(ROWS):
        for col in range(COLS):
            x1 = col * CELL_SIZE
            y1 = row * CELL_SIZE
            x2 = x1 + CELL_SIZE
            y2 = y1 + CELL_SIZE

            color = EMPTY_COLOR
            if grid[row][col] == 1:
                color = WALL_COLOR
            elif (row, col) == START:
                color = START_COLOR
            elif (row, col) == TARGET:
                color = TARGET_COLOR

            # Draw cell rectangle
            canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="gray")

            # Draw the cell value (0 or 1)
            if (row, col) != START and (row, col) != TARGET:
                canvas.create_text(
                    x1 + CELL_SIZE/2,
                    y1 + CELL_SIZE/2,
                    text=str(grid[row][col]),
                    fill="blue",
                    font=("Arial", 12)
                )

def main():
    root = tk.Tk()
    root.title("AI Pathfinder Grid")

    canvas = tk.Canvas(root, width=COLS*CELL_SIZE, height=ROWS*CELL_SIZE)
    canvas.pack()

    draw_grid(canvas)

    root.mainloop()

if __name__ == "__main__":
    main()
