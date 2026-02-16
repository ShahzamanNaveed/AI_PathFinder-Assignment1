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
FRONTIER_COLOR = "lightblue"
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

def draw_grid(canvas, frontier=set(), explored=set(), path=set()):
    canvas.delete("all")  # clear previous drawings
    for row in range(ROWS):
        for col in range(COLS):
            x1 = col * CELL_SIZE
            y1 = row * CELL_SIZE
            x2 = x1 + CELL_SIZE
            y2 = y1 + CELL_SIZE

            # Determine cell color
            color = EMPTY_COLOR
            if grid[row][col] == 1:
                color = WALL_COLOR
            elif (row, col) == START:
                color = START_COLOR
            elif (row, col) == TARGET:
                color = TARGET_COLOR
            elif (row, col) in path:
                color = PATH_COLOR
            elif (row, col) in explored:
                color = EXPLORED_COLOR
            elif (row, col) in frontier:
                color = FRONTIER_COLOR

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

# ------------------ BFS Function ------------------
def bfs(canvas):
    queue = deque()
    queue.append([START])  
    explored = set()

    while queue:
        path = queue.popleft()
        current = path[-1]  # current node = last node in path

        # Mark as explored
        explored.add(current)

        # Prepare frontier set for visualization
        frontier = set(p[-1] for p in queue)

        # Draw the current state
        draw_grid(canvas, frontier=frontier, explored=explored)
        canvas.update()
        time.sleep(0.2) 

        # Check if target reached
        if current == TARGET:
            draw_grid(canvas, path=set(path))
            canvas.update()
            return path

        # Expand neighbors (clockwise order)
        row, col = current
        neighbors = [
            (row-1, col),       # Up
            (row, col+1),       # Right
            (row+1, col),       # Bottom
            (row+1, col+1),     # Bottom-Right
            (row, col-1),       # Left
            (row-1, col-1)      # Top-Left
        ]

        for r, c in neighbors:
            if 0 <= r < ROWS and 0 <= c < COLS:
                if grid[r][c] == 0 and (r, c) not in explored and (r, c) not in [p[-1] for p in queue]:
                    queue.append(path + [(r, c)])  # append new path with neighbor

    return None  

# ------------------ DFS Algorithm ------------------
def dfs(canvas):
    stack = []
    stack.append([START])
    explored = set()
    
    while stack:
        path = stack.pop()
        current = path[-1]
        explored.add(current)
        frontier = set(p[-1] for p in stack)
        
        draw_grid(canvas, frontier=frontier, explored=explored)
        canvas.update()
        time.sleep(0.2)

        if current == TARGET:
            draw_grid(canvas, path=set(path))
            canvas.update()
            return path
        row, col = current
        neighbors = [
            (row-1, col), (row, col+1), (row+1, col),
            (row+1, col+1), (row, col-1), (row-1, col-1)
        ]

        for r, c in neighbors:
            if 0 <= r < ROWS and 0 <= c < COLS:
                if grid[r][c] == 0 and (r, c) not in explored and (r, c) not in [p[-1] for p in stack]:
                    stack.append(path + [(r, c)])
    return None

# ------------------ Run Selected Algorithm ------------------
def run_algorithm():
    algo = algo_var.get()  
    if algo == "BFS":
        bfs(canvas)
    elif algo == "DFS":
        dfs(canvas)

# ------------------ Main GUI ------------------
root = tk.Tk()
root.title("AI Pathfinder")

# Canvas for grid
canvas = tk.Canvas(root, width=COLS*CELL_SIZE, height=ROWS*CELL_SIZE)
canvas.pack()

# Dropdown menu to select algorithm
algo_var = tk.StringVar(root)
algo_var.set("BFS") 
algo_menu = tk.OptionMenu(root, algo_var, "BFS", "DFS")
algo_menu.pack(pady=10)

# Button to run selected algorithm
run_button = tk.Button(root, text="Run Search", command=run_algorithm)
run_button.pack(pady=5)

# Draw initial grid
draw_grid(canvas)

root.mainloop()