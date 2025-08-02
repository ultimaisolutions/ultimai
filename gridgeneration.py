import json

def generate_rect_grid(corners, Vspacing, wall_offset=0.2, zy_step=0.1):
    """
    corners: list of 4 (x, y) tuples in order
             [LL, UL, UR, LR]
    Vspacing: float, desired spacing both vertically and horizontally
    wall_offset: float, fixed clearance from every wall
    zy_step: float, how much to nudge initial column up on each retry
    """
    # Unpack and derive bounds
    (x0, y0), (_, y1), (x1, _), _ = corners
    min_x, max_x = x0, x1
    min_y, max_y = y0, y1

    # Inner bounds after wall offset
    x_start = min_x + wall_offset
    x_limit = max_x - wall_offset
    y_min = min_y + wall_offset
    y_max = max_y - wall_offset

    # 1) Find a vertical column that fits
    zy = 0.0
    while True:
        col = []
        y = y_min + zy
        # if first point already out of vertical range, try next zy
        if y > y_max:
            zy += zy_step
            continue

        # build up column
        ok = True
        while True:
            # distances to walls
            Dlow   = y - min_y
            Dup    = max_y - y
            Dleft  = x_start - min_x
            Dright = max_x - x_start

            if min(Dlow, Dup, Dleft, Dright) < wall_offset:
                ok = False
                break

            col.append((x_start, y))

            # next y
            y_next = y + Vspacing
            if y_next > y_max:
                break
            y = y_next

        if ok and col:
            break
        zy += zy_step

    # 2) Replicate that column horizontally
    grid = []
    col_index = 0
    while True:
        x = x_start + col_index * Vspacing
        Dright = max_x - x

        # if too close, drop and stop
        if Dright < wall_offset:
            break

        # add this entire column
        for (_, y_pt) in col:
            grid.append((x, y_pt))

        col_index += 1
        # if exactly at the wall offset, stop after including it
        if abs(Dright - wall_offset) < 1e-8:
            break

    # 3) Compute summary details
    num_pts = len(grid)
    # for each point, compute nearest‐wall distance, then average
    bdists = [
        min(px - min_x, max_x - px, py - min_y, max_y - py)
        for (px, py) in grid
    ]
    avg_bd = sum(bdists) / num_pts if num_pts else 0.0

    # 4) Package into JSON‐friendly structure
    rect_list = [[x0, y0], [x0, y1], [x1, y1], [x1, y0]]

    def fmt(v): return round(v, 2)

    result = {
        "Rectangle": rect_list,
        "Grid": [[fmt(px), fmt(py)] for px, py in grid],
        "Details": {
            "spacing": fmt(Vspacing),
            "num_points": num_pts,
            "avg_point_distance": fmt(Vspacing),
            "avg_boundary_distance": fmt(avg_bd)
        }
    }
    return result

if __name__ == "__main__":
    # --- example usage ---
    corners = [(0, 0), (0, 10), (30, 10), (30, 0)]
    Vspacing = 1.8

    grid_data = generate_rect_grid(corners, Vspacing)
    print(json.dumps(grid_data, indent=2))
