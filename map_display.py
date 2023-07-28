import random
import tkinter as tk
from tkinter import font

# Reads a binary file and displays the content as a map with unique colors per value
# offset = 5
start_offset = 0
start_width = 60

# file_path = "/tmp/CursedKingdoms/data/TOWN-A"
file_path = "/tmp/CursedKingdoms/data/Bak/MAP0-0"

value_to_color = {}


def read_file_as_map(file_path):
    with open(file_path, 'rb') as file:
        byte_pairs = file.read()

    return [hex(byte_pair)[2:].upper().zfill(2) for byte_pair in byte_pairs]

    # return [f'{byte_pairs[i+1]:02X}' for i in range(0, len(byte_pairs), 2)]


def generate_random_color():
    return f'#{random.randint(0, 0xFFFFFF):06x}'


def check_byte_pair(map_array):
    for i, value in enumerate(map_array):
        if i % 2 == 0:
            if value != '00':
                break

    filtered_array = []
    for i, value in enumerate(map_array):
        if i % 2 == 1:
            filtered_array.append(value)

    return filtered_array


def set_colors(map_array):
    unique_values = list(set(map_array))
    return {value: generate_random_color() for value in unique_values}


def draw_map(canvas, row_width, cell_size, offset):
    rows = [map_array[i:i+row_width] for i in range(offset, len(map_array), row_width)]

    fixed_width_font = font.Font(family='Courier New', size=8)

    for row_index, row in enumerate(rows):
        for col_index, element in enumerate(row):
            text = str(element)
            bg_color = value_to_color.get(text, 'white')
            x1 = col_index * cell_size
            y1 = row_index * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size
            canvas.create_rectangle(x1, y1, x2, y2, fill=bg_color)
            canvas.create_text(x1 + cell_size // 2, y1 + cell_size // 2, text=text, font=fixed_width_font)


def redraw_map(canvas, row_width_var, cell_size, offset_var):
    try:
        row_width = int(row_width_var.get())
        if row_width > 0:
            offset = int(offset_var.get())
            canvas.delete("all")  # Clear the canvas
            draw_map(canvas, row_width, cell_size, offset)
    except ValueError:
        pass


def increase_row_width(row_width_var):
    try:
        current_width = int(row_width_var.get())
        row_width_var.set(current_width + 1)
    except ValueError:
        pass


def decrease_row_width(row_width_var):
    try:
        current_width = int(row_width_var.get())
        if current_width > 1:
            row_width_var.set(current_width - 1)
    except ValueError:
        pass


def create_map_window(map_array, offset=0, row_width=16, cell_size=20):
    window = tk.Tk()
    window.title('Map Data')

    canvas = tk.Canvas(window, width=cell_size * row_width, height=1200)  # Adjust the canvas size as needed
    canvas.grid(row=1, column=0, columnspan=5)  # Place canvas in the first row, spanning 3 columns

    # Create a number input field to change row_width
    row_width_var = tk.StringVar(value=row_width)
    row_width_entry = tk.Entry(window, textvariable=row_width_var, width=5)  # Adjust the width of the entry field
    row_width_entry.grid(row=0, column=0)

    # Create up and down buttons for changing row_width
    up_button = tk.Button(window, text="▲", command=lambda: (increase_row_width(row_width_var), redraw_map(canvas, row_width_var, cell_size, offset_var)))
    down_button = tk.Button(window, text="▼", command=lambda: (decrease_row_width(row_width_var), redraw_map(canvas, row_width_var, cell_size, offset_var)))
    up_button.grid(row=0, column=1)
    down_button.grid(row=0, column=2)

    # Create a number input field to change offset
    offset_var = tk.StringVar(value=offset)
    offset_entry = tk.Entry(window, textvariable=offset_var, width=5)  # Adjust the width of the entry field
    offset_entry.grid(row=0, column=3)

    # Create a button to redraw the map
    redraw_button = tk.Button(window, text="Redraw Map", command=lambda: redraw_map(canvas, row_width_var, cell_size, offset_var))
    redraw_button.grid(row=0, column=4, columnspan=2)  # Place the button in the second row, spanning 2 columns

    # Draw map initially
    draw_map(canvas, row_width, cell_size, offset)

    window.mainloop()


if __name__ == "__main__":
    map_array = read_file_as_map(file_path)
    map_array = check_byte_pair(map_array)
    value_to_color = set_colors(map_array)
    create_map_window(map_array, start_offset, start_width)
