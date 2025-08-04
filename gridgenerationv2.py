import json
import re



## works only in n8n!!!!!!

# 1) Grab & normalize the raw query string
raw = query.to_py() if hasattr(query, "to_py") else query
raw = str(raw)

# 2) Parse exactly four “(x, y)” pairs
coords = re.findall(
    r'\(\s*([+-]?\d*\.?\d+)\s*,\s*([+-]?\d*\.?\d+)\s*\)', raw
)
if len(coords) < 4:
    raise ValueError(f"Expected 4 coords, got {len(coords)} in {raw!r}")
rectangle = [(float(x), float(y)) for x, y in coords[:4]]

# 3) Extract spacing under either “spacing” or “Vspacing”
m = re.search(
    r'\b(?:Vspacing|spacing)\s*[:=]\s*([+-]?\d*\.?\d+)\b',
    raw,
    re.IGNORECASE
)
if not m:
    raise ValueError(f"No spacing found in: {raw!r}")
Vspacing = float(m.group(1))

# 4) Unpack rectangle bounds
xs, ys    = [p[0] for p in rectangle], [p[1] for p in rectangle]
xmin, xmax = min(xs), max(xs)
ymin, ymax = min(ys), max(ys)

# 5) Fixed wall offset
offset       = 0.2
usable_w, usable_h = xmax - xmin - 2*offset, ymax - ymin - 2*offset

# 6) How many columns/rows fit
num_cols = int(usable_w  // Vspacing) + 1
num_rows = int(usable_h // Vspacing) + 1

# 7) Center the grid inside the usable area
total_w  = (num_cols - 1) * Vspacing
total_h  = (num_rows - 1) * Vspacing
x_start  = xmin + offset + (usable_w - total_w) / 2
y_start  = ymin + offset + (usable_h - total_h) / 2

# 8) Build grid points
grid_points = []
for i in range(num_cols):
    x = x_start + i * Vspacing
    for j in range(num_rows):
        y = y_start + j * Vspacing
        grid_points.append([round(x, 1), round(y, 1)])

# 9) Compute average boundary distance
total_bd = sum(
    min(x - xmin, xmax - x, y - ymin, ymax - y)
    for x, y in grid_points
)
avg_bd = round(total_bd / len(grid_points), 2) if grid_points else 0

# 10) Package the result
result = {
    "Rectangle": rectangle,
    "Grid":      grid_points,
    "Details": {
        "spacing":               round(Vspacing, 2),
        "num_points":            len(grid_points),
        "avg_point_distance":    round(Vspacing, 2),
        "avg_boundary_distance": avg_bd
    }
}

# 11) Return the single JSON string as the node’s output
return json.dumps(result)
##works only in n8n!!!!!!
