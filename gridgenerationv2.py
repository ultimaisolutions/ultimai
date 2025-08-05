import json
import pandas as pd
def generate_rect_grid(rectangle, Vspacing):
    xs = [p[0] for p in rectangle]
    ys = [p[1] for p in rectangle]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)

    offset = 0.2
    usable_width = xmax - xmin - 2 * offset
    usable_height = ymax - ymin - 2 * offset

    # How many full steps of spacing fit in the usable area
    num_cols = int(usable_width // Vspacing) + 1
    num_rows = int(usable_height // Vspacing) + 1

    total_grid_width = (num_cols - 1) * Vspacing
    total_grid_height = (num_rows - 1) * Vspacing

    # Center the grid horizontally and vertically within usable bounds
    x_start = xmin + offset + (usable_width - total_grid_width) / 2
    y_start = ymin + offset + (usable_height - total_grid_height) / 2

    grid_points = []
    for i in range(num_cols):
        x = x_start + i * Vspacing
        for j in range(num_rows):
            y = y_start + j * Vspacing
            grid_points.append([round(x, 1), round(y, 1)])

    # Details
    def avg_boundary_distance(points):
        total = 0
        for x, y in points:
            Dleft = x - xmin
            Dright = xmax - x
            Dlower = y - ymin
            Dupper = ymax - y
            total += min(Dleft, Dright, Dlower, Dupper)
        return round(total / len(points), 2) if points else 0

    result = {
        "Rectangle": rectangle,
        "Grid": grid_points,
        "Details": {
            "spacing": round(Vspacing, 2),
            "num_points": len(grid_points),
            "avg_point_distance": round(Vspacing, 2),
            "avg_boundary_distance": avg_boundary_distance(grid_points)
        }
    }

    return result  # ← returns a Python dict



if __name__ == "__main__":
    # --- Example usage ---
    corners = [(0, 0), (0, 10), (30, 10), (30, 0)]
    Vspacing = 1.8

    output = generate_rect_grid(corners, Vspacing)


    data = output

    # --- Extract data ---
    grid_points = data["Grid"]
    rectangle_coords = data["Rectangle"]
    details = data["Details"]

    # --- Create DataFrames ---
    df_grid = pd.DataFrame(grid_points, columns=["X", "Y"])

    df_rectangle = pd.DataFrame(rectangle_coords, columns=["X", "Y"])
    df_details = pd.DataFrame([details])

    # --- Write to Excel ---
    with pd.ExcelWriter("grid_output.xlsx", engine="openpyxl") as writer:
        df_grid.to_excel(writer, sheet_name="Grid Points")
        df_rectangle.to_excel(writer, sheet_name="Rectangle", index=False)
        df_details.to_excel(writer, sheet_name="Details", index=False)

    print("✅ Excel file 'grid_output.xlsx' created successfully.")