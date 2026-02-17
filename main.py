import tkinter as tk
import time
from collections import deque
import heapq

#  CONFIGURATION
ROWS       = 10
COLS       = 10
CELL_SIZE  = 40
STEP_DELAY = 0.1   # seconds between animation frames

DIAG_COST = 1.414

#  COLORS
COLOR = {
    "empty"       : "#F0F0F0",
    "wall"        : "#2C2C2C",
    "start"       : "#27AE60",
    "target"      : "#E74C3C",
    "frontier"    : "#AED6F1",
    "explored"    : "#2980B9",
    "path"        : "#8E44AD",
    # Bidirectional-specific
    "fwd_frontier": "#AED6F1",   # light blue  – forward  frontier
    "bwd_frontier": "#FADBD8",   # light red   – backward frontier
    "fwd_explored": "#2980B9",   # blue        – forward  explored
    "bwd_explored": "#C0392B",   # dark red    – backward explored
    "meet"        : "#F39C12",   # orange      – meeting node
}

#  STATIC GRID  (0 = empty, 1 = wall)
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
    [0,0,0,0,0,0,0,0,0,0],
]

START  = (0, 0)
TARGET = (9, 9)

DIRECTIONS = [
    (-1,  0),   # Up
    ( 0,  1),   # Right
    ( 1,  0),   # Bottom
    ( 1,  1),   # Bottom-Right (diagonal)
    ( 0, -1),   # Left
    (-1, -1),   # Top-Left (diagonal)
]

DIAG_PAIRS = {(1, 1), (-1, -1)}

#  HELPERS

def get_neighbors(row, col):
    """Yield valid (r, c, cost) neighbours in the required direction order."""
    for dr, dc in DIRECTIONS:
        r, c = row + dr, col + dc
        if 0 <= r < ROWS and 0 <= c < COLS and grid[r][c] == 0:
            cost = DIAG_COST if (dr, dc) in DIAG_PAIRS else 1.0
            yield r, c, cost

#  DRAWING

def draw_grid(canvas, frontier=frozenset(), explored=frozenset(),
              path=frozenset(), status=""):
    canvas.delete("all")

    for row in range(ROWS):
        for col in range(COLS):
            x1, y1 = col * CELL_SIZE, row * CELL_SIZE
            x2, y2 = x1 + CELL_SIZE, y1 + CELL_SIZE
            # Determine cell color (priority order matters)
            if (row, col) == START:
                color = COLOR["start"]
            elif (row, col) == TARGET:
                color = COLOR["target"]
            elif grid[row][col] == 1:
                color = COLOR["wall"]
            elif (row, col) in path:
                color = COLOR["path"]
            elif (row, col) in explored:
                color = COLOR["explored"]
            elif (row, col) in frontier:
                color = COLOR["frontier"]
            else:
                color = COLOR["empty"]

            canvas.create_rectangle(x1, y1, x2, y2,
                                    fill=color, outline="#AAAAAA", width=1)
            # Cell label
            if (row, col) == START:
                label, fg = "S", "white"
            elif (row, col) == TARGET:
                label, fg = "T", "white"
            elif grid[row][col] == 1:
                label, fg = "■", "#888888"
            else:
                label, fg = "", "black"

            if label:
                canvas.create_text(
                    x1 + CELL_SIZE // 2,
                    y1 + CELL_SIZE // 2,
                    text=label, fill=fg,
                    font=("Arial", 14, "bold")
                )

    # Status bar below grid
    canvas.create_text(
        COLS * CELL_SIZE // 2,
        ROWS * CELL_SIZE + 15,
        text=status, fill="#333333",
        font=("Arial", 10, "italic")
    )

#  DRAWING – Bidirectional variant
def draw_grid_bidir(canvas,
                    fwd_frontier=frozenset(), bwd_frontier=frozenset(),
                    fwd_explored=frozenset(), bwd_explored=frozenset(),
                    path=frozenset(), meet=None, status=""):
    canvas.delete("all")

    for row in range(ROWS):
        for col in range(COLS):
            x1, y1 = col * CELL_SIZE, row * CELL_SIZE
            x2, y2 = x1 + CELL_SIZE,  y1 + CELL_SIZE
            cell   = (row, col)

            if cell == START:
                color = COLOR["start"]
            elif cell == TARGET:
                color = COLOR["target"]
            elif grid[row][col] == 1:
                color = COLOR["wall"]
            elif cell in path:
                color = COLOR["path"]
            elif cell == meet:
                color = COLOR["meet"]
            elif cell in fwd_explored and cell in bwd_explored:
                # Overlap – blend visually with the meeting colour
                color = COLOR["meet"]
            elif cell in fwd_explored:
                color = COLOR["fwd_explored"]
            elif cell in bwd_explored:
                color = COLOR["bwd_explored"]
            elif cell in fwd_frontier:
                color = COLOR["fwd_frontier"]
            elif cell in bwd_frontier:
                color = COLOR["bwd_frontier"]
            else:
                color = COLOR["empty"]

            canvas.create_rectangle(x1, y1, x2, y2,
                                    fill=color, outline="#AAAAAA", width=1)

            if cell == START:
                label, fg = "S", "white"
            elif cell == TARGET:
                label, fg = "T", "white"
            elif grid[row][col] == 1:
                label, fg = "■", "#888888"
            else:
                label, fg = "", "black"

            if label:
                canvas.create_text(x1 + CELL_SIZE // 2, y1 + CELL_SIZE // 2,
                                   text=label, fill=fg,
                                   font=("Arial", 14, "bold"))

    canvas.create_text(COLS * CELL_SIZE // 2, ROWS * CELL_SIZE + 15,
                       text=status, fill="#333333",
                       font=("Arial", 10, "italic"))

# ──────────────────────────────────────────
#  BFS
# ──────────────────────────────────────────
def bfs(canvas):
    queue    = deque([[START]])
    explored = set()
    in_queue = {START}

    while queue:
        path    = queue.popleft()
        current = path[-1]
        in_queue.discard(current)

        if current in explored:
            continue
        explored.add(current)

        draw_grid(canvas,
                  frontier=in_queue.copy(),
                  explored=explored,
                  status=f"BFS – exploring {current}")
        canvas.update()
        time.sleep(STEP_DELAY)

        if current == TARGET:
            draw_grid(canvas, path=set(path), status="BFS – Path Found! ✓")
            canvas.update()
            return path

        row, col = current
        for r, c, _ in get_neighbors(row, col):
            if (r, c) not in explored and (r, c) not in in_queue:
                queue.append(path + [(r, c)])
                in_queue.add((r, c))

    draw_grid(canvas, status="BFS – No path found ✗")
    canvas.update()
    return None

# ──────────────────────────────────────────
#  DFS
# ──────────────────────────────────────────
def dfs(canvas):
    stack    = [[START]]
    explored = set()
    in_stack = {START}

    while stack:
        path    = stack.pop()
        current = path[-1]
        in_stack.discard(current)

        if current in explored:
            continue
        explored.add(current)

        draw_grid(canvas,
                  frontier=in_stack.copy(),
                  explored=explored,
                  status=f"DFS – exploring {current}")
        canvas.update()
        time.sleep(STEP_DELAY)

        if current == TARGET:
            draw_grid(canvas, path=set(path), status="DFS – Path Found! ✓")
            canvas.update()
            return path

        row, col = current
        for r, c, _ in get_neighbors(row, col):
            if (r, c) not in explored and (r, c) not in in_stack:
                stack.append(path + [(r, c)])
                in_stack.add((r, c))

    draw_grid(canvas, status="DFS – No path found ✗")
    canvas.update()
    return None

# ──────────────────────────────────────────
#  DLS  (Depth-Limited Search)
# ──────────────────────────────────────────
def dls(canvas, limit):
    stack    = [([START], 0)]   # (path, depth)
    explored = set()
    in_stack = {START}

    while stack:
        path, depth = stack.pop()
        current     = path[-1]
        in_stack.discard(current)

        if current in explored:
            continue
        explored.add(current)

        draw_grid(canvas,
                  frontier=in_stack.copy(),
                  explored=explored,
                  status=f"DLS – exploring {current}  depth={depth}/{limit}")
        canvas.update()
        time.sleep(STEP_DELAY)

        if current == TARGET:
            draw_grid(canvas, path=set(path),
                      status=f"DLS – Path Found! ✓  depth={depth}")
            canvas.update()
            return path

        # Do NOT expand beyond the depth limit
        if depth >= limit:
            continue

        row, col = current
        for r, c, _ in get_neighbors(row, col):
            if (r, c) not in explored and (r, c) not in in_stack:
                stack.append((path + [(r, c)], depth + 1))
                in_stack.add((r, c))

    draw_grid(canvas,
              status=f"DLS – No path found within depth limit {limit} ✗")
    canvas.update()
    return None

# ──────────────────────────────────────────
#  IDDFS  (Iterative Deepening DFS)
# ──────────────────────────────────────────
def iddfs(canvas):
    max_possible = ROWS * COLS   # absolute upper bound on any useful path length

    for limit in range(max_possible + 1):
        # ── Announce the new iteration ──
        draw_grid(canvas, status=f"IDDFS – starting iteration with depth limit = {limit}")
        canvas.update()
        time.sleep(STEP_DELAY)

        # ── Run one DLS pass, collecting state for animation ──
        stack    = [([START], 0)]   # (path, depth)
        explored = set()
        in_stack = {START}
        found    = False

        while stack:
            path, depth = stack.pop()
            current     = path[-1]
            in_stack.discard(current)

            if current in explored:
                continue
            explored.add(current)

            draw_grid(canvas,
                      frontier=in_stack.copy(),
                      explored=explored,
                      status=f"IDDFS – limit={limit}  exploring {current}  depth={depth}")
            canvas.update()
            time.sleep(STEP_DELAY)

            if current == TARGET:
                draw_grid(canvas, path=set(path),
                          status=f"IDDFS – Path Found! ✓  depth limit={limit}  path length={len(path)}")
                canvas.update()
                return path

            if depth < limit:
                row, col = current
                for r, c, _ in get_neighbors(row, col):
                    if (r, c) not in explored and (r, c) not in in_stack:
                        stack.append((path + [(r, c)], depth + 1))
                        in_stack.add((r, c))

        # ── Iteration exhausted without finding target ──
        draw_grid(canvas,
                  explored=explored,
                  status=f"IDDFS – limit={limit} exhausted, deepening…")
        canvas.update()
        time.sleep(STEP_DELAY * 1.5)

    draw_grid(canvas, status="IDDFS – No path found ✗")
    canvas.update()
    return None

# ──────────────────────────────────────────
#  BIDIRECTIONAL SEARCH
# ──────────────────────────────────────────

def bidirectional(canvas):
    fwd_queue    = deque([START])
    bwd_queue    = deque([TARGET])

    fwd_frontier = {START}          # nodes sitting in fwd_queue
    bwd_frontier = {TARGET}         # nodes sitting in bwd_queue

    fwd_explored = {}               # node -> parent (None for START)
    bwd_explored = {}               # node -> parent (None for TARGET)

    def reconstruct(meet_node):
        """Build full path START → meet_node → TARGET."""
        # Forward half: trace parents back to START then reverse
        fwd_half = []
        node = meet_node
        while node is not None:
            fwd_half.append(node)
            node = fwd_explored.get(node)
        fwd_half.reverse()

        # Backward half: trace parents back to TARGET
        bwd_half = []
        node = bwd_explored.get(meet_node)   # skip meet_node (already in fwd_half)
        while node is not None:
            bwd_half.append(node)
            node = bwd_explored.get(node)
        bwd_half.append(TARGET)

        return fwd_half + bwd_half

    meet_node = None

    while fwd_queue or bwd_queue:

        # ── Expand ONE step from the FORWARD frontier ──────────────────
        if fwd_queue:
            current = fwd_queue.popleft()
            fwd_frontier.discard(current)   # leaving frontier → becomes explored
            fwd_explored[current] = fwd_explored.get(current)  # preserve parent

            draw_grid_bidir(canvas,
                            fwd_frontier=fwd_frontier.copy(),
                            bwd_frontier=bwd_frontier.copy(),
                            fwd_explored=set(fwd_explored),
                            bwd_explored=set(bwd_explored),
                            status=f"Bidir – FWD exploring {current}")
            canvas.update()
            time.sleep(STEP_DELAY)

            # Meeting check: current was already reached by backward search
            if current in bwd_explored:
                meet_node = current
                break

            row, col = current
            for r, c, _ in get_neighbors(row, col):
                if (r, c) not in fwd_explored and (r, c) not in fwd_frontier:
                    fwd_explored[(r, c)] = current   # record parent now
                    fwd_frontier.add((r, c))
                    fwd_queue.append((r, c))

        # ── Expand ONE step from the BACKWARD frontier ─────────────────
        if bwd_queue:
            current = bwd_queue.popleft()
            bwd_frontier.discard(current)
            bwd_explored[current] = bwd_explored.get(current)

            draw_grid_bidir(canvas,
                            fwd_frontier=fwd_frontier.copy(),
                            bwd_frontier=bwd_frontier.copy(),
                            fwd_explored=set(fwd_explored),
                            bwd_explored=set(bwd_explored),
                            status=f"Bidir – BWD exploring {current}")
            canvas.update()
            time.sleep(STEP_DELAY)

            # Meeting check: current was already reached by forward search
            if current in fwd_explored:
                meet_node = current
                break

            row, col = current
            for r, c, _ in get_neighbors(row, col):
                if (r, c) not in bwd_explored and (r, c) not in bwd_frontier:
                    bwd_explored[(r, c)] = current
                    bwd_frontier.add((r, c))
                    bwd_queue.append((r, c))

    # ── Done ───────────────────────────────────────────────────────────
    if meet_node is not None:
        full_path = reconstruct(meet_node)
        draw_grid_bidir(canvas,
                        fwd_explored=set(fwd_explored),
                        bwd_explored=set(bwd_explored),
                        path=set(full_path),
                        meet=meet_node,
                        status=f"Bidir – Path Found! ✓  meeting node={meet_node}  length={len(full_path)}")
        canvas.update()
        return full_path

    draw_grid_bidir(canvas,
                    fwd_explored=set(fwd_explored),
                    bwd_explored=set(bwd_explored),
                    status="Bidir – No path found ✗")
    canvas.update()
    return None

# ──────────────────────────────────────────
#  UCS
# ──────────────────────────────────────────
def ucs(canvas):
    counter   = 0                          # tie-breaker to avoid comparing lists
    pq        = [(0.0, counter, [START])]
    explored  = set()
    best_cost = {START: 0.0}

    while pq:
        cost, _, path = heapq.heappop(pq)
        current       = path[-1]

        if current in explored:
            continue
        explored.add(current)

        frontier = {entry[2][-1] for entry in pq}
        draw_grid(canvas,
                  frontier=frontier,
                  explored=explored,
                  status=f"UCS – exploring {current}  cost={cost:.2f}")
        canvas.update()
        time.sleep(STEP_DELAY)

        if current == TARGET:
            draw_grid(canvas, path=set(path),
                      status=f"UCS – Path Found! ✓  Total cost = {cost:.2f}")
            canvas.update()
            return path

        row, col = current
        for r, c, move_cost in get_neighbors(row, col):
            if (r, c) not in explored:
                new_cost = cost + move_cost
                if new_cost < best_cost.get((r, c), float('inf')):
                    best_cost[(r, c)] = new_cost
                    counter += 1
                    heapq.heappush(pq, (new_cost, counter, path + [(r, c)]))

    draw_grid(canvas, status="UCS – No path found ✗")
    canvas.update()
    return None


# ──────────────────────────────────────────
#  RUN BUTTON CALLBACK
# ──────────────────────────────────────────
def run_algorithm():
    global START, TARGET

    # ── Parse start and target from user input ──
    try:
        sr, sc = int(start_row_var.get()), int(start_col_var.get())
        tr, tc = int(target_row_var.get()), int(target_col_var.get())
    except ValueError:
        draw_grid(canvas, status="Error: row/col must be integers (0–9)")
        canvas.update()
        return

    for label, r, c in [("Start", sr, sc), ("Target", tr, tc)]:
        if not (0 <= r < ROWS and 0 <= c < COLS):
            draw_grid(canvas, status=f"Error: {label} ({r},{c}) is out of bounds (0–{ROWS-1})")
            canvas.update()
            return
        if grid[r][c] == 1:
            draw_grid(canvas, status=f"Error: {label} ({r},{c}) is a wall")
            canvas.update()
            return

    if (sr, sc) == (tr, tc):
        draw_grid(canvas, status="Error: Start and Target must be different cells")
        canvas.update()
        return

    START  = (sr, sc)
    TARGET = (tr, tc)

    draw_grid(canvas, status="Starting…")
    canvas.update()
    run_btn.config(state=tk.DISABLED)
    root.update()

    algo = algo_var.get()
    try:
        if   algo == "BFS": bfs(canvas)
        elif algo == "Bidir": bidirectional(canvas)
        elif algo == "DFS": dfs(canvas)
        elif algo == "UCS": ucs(canvas)
        elif algo == "IDDFS": iddfs(canvas)
        elif algo == "DLS":
            try:
                limit = int(depth_var.get())
                if limit < 0:
                    raise ValueError
            except ValueError:
                draw_grid(canvas, status="DLS – Please enter a valid depth limit (integer ≥ 0)")
                canvas.update()
                return
            dls(canvas, limit)
    finally:
        run_btn.config(state=tk.NORMAL)

# ──────────────────────────────────────────
#  LEGEND
# ──────────────────────────────────────────
def build_legend(parent):
    frame = tk.Frame(parent, bg="#FAFAFA", bd=1, relief=tk.GROOVE)
    frame.pack(fill=tk.X, padx=10, pady=(0, 10))

    items = [
        (COLOR["start"],        "Start (S)"),
        (COLOR["target"],       "Target (T)"),
        (COLOR["wall"],         "Wall"),
        (COLOR["fwd_frontier"], "Fwd Frontier"),
        (COLOR["bwd_frontier"], "Bwd Frontier"),
        (COLOR["fwd_explored"], "Fwd Explored"),
        (COLOR["bwd_explored"], "Bwd Explored"),
        (COLOR["meet"],         "Meeting Node"),
        (COLOR["path"],         "Final Path"),
    ]

    for i, (color, label) in enumerate(items):
        tk.Label(frame, bg=color, width=2,
                 relief=tk.RAISED).grid(row=0, column=i*2,   padx=(8, 2), pady=5)
        tk.Label(frame, text=label, bg="#FAFAFA",
                 font=("Arial", 9)).grid(row=0, column=i*2+1, padx=(0, 10))

# ──────────────────────────────────────────
#  MAIN WINDOW
# ──────────────────────────────────────────
root = tk.Tk()
root.title("AI Pathfinder – BFS / DFS / UCS / DLS / IDDFS / Bidir")
root.resizable(False, False)
root.configure(bg="#FAFAFA")

# Title
tk.Label(root, text="AI Pathfinder",
         font=("Arial", 16, "bold"), bg="#FAFAFA").pack(pady=(10, 4))

# Canvas (extra 30 px for status bar)
canvas = tk.Canvas(root,
                   width=COLS * CELL_SIZE,
                   height=ROWS * CELL_SIZE + 30,
                   bg="#FAFAFA", bd=0, highlightthickness=0)
canvas.pack(padx=10)

# Controls row
ctrl = tk.Frame(root, bg="#FAFAFA")
ctrl.pack(pady=8)

tk.Label(ctrl, text="Algorithm:", bg="#FAFAFA",
         font=("Arial", 11)).grid(row=0, column=0, padx=6)

algo_var = tk.StringVar(root)
algo_var.set("BFS")
tk.OptionMenu(ctrl, algo_var, "BFS", "DFS", "UCS", "DLS", "IDDFS", "Bidir").grid(row=0, column=1, padx=6)

# Depth limit row (shown only for DLS)
depth_frame = tk.Frame(root, bg="#FAFAFA")
depth_frame.pack(pady=(0, 4))
tk.Label(depth_frame, text="Depth Limit (DLS):", bg="#FAFAFA",
         font=("Arial", 10)).grid(row=0, column=0, padx=6)
depth_var = tk.StringVar(root)
depth_var.set("15")
depth_entry = tk.Entry(depth_frame, textvariable=depth_var, width=5,
                       font=("Arial", 11), justify="center")
depth_entry.grid(row=0, column=1, padx=4)
tk.Label(depth_frame, text="(used by DLS only)", bg="#FAFAFA",
         font=("Arial", 9), fg="#888888").grid(row=0, column=2, padx=6)

# Start / Target input row
st_frame = tk.Frame(root, bg="#FAFAFA")
st_frame.pack(pady=(0, 4))

tk.Label(st_frame, text="Start (row, col):", bg="#FAFAFA",
         font=("Arial", 10)).grid(row=0, column=0, padx=(8,2))
start_row_var = tk.StringVar(root); start_row_var.set("0")
start_col_var = tk.StringVar(root); start_col_var.set("0")
tk.Entry(st_frame, textvariable=start_row_var, width=3,
         font=("Arial", 11), justify="center").grid(row=0, column=1, padx=2)
tk.Label(st_frame, text=",", bg="#FAFAFA",
         font=("Arial", 11)).grid(row=0, column=2)
tk.Entry(st_frame, textvariable=start_col_var, width=3,
         font=("Arial", 11), justify="center").grid(row=0, column=3, padx=2)

tk.Label(st_frame, text="    Target (row, col):", bg="#FAFAFA",
         font=("Arial", 10)).grid(row=0, column=4, padx=(16,2))
target_row_var = tk.StringVar(root); target_row_var.set("9")
target_col_var = tk.StringVar(root); target_col_var.set("9")
tk.Entry(st_frame, textvariable=target_row_var, width=3,
         font=("Arial", 11), justify="center").grid(row=0, column=5, padx=2)
tk.Label(st_frame, text=",", bg="#FAFAFA",
         font=("Arial", 11)).grid(row=0, column=6)
tk.Entry(st_frame, textvariable=target_col_var, width=3,
         font=("Arial", 11), justify="center").grid(row=0, column=7, padx=2)

run_btn = tk.Button(ctrl, text="▶  Run Search",
                    command=run_algorithm,
                    bg="#2980B9", fg="white",
                    font=("Arial", 11, "bold"),
                    relief=tk.FLAT, padx=12, pady=4)
run_btn.grid(row=0, column=2, padx=10)

# Legend
build_legend(root)
# Initial draw
draw_grid(canvas, status="Select an algorithm and press Run Search")

root.mainloop()