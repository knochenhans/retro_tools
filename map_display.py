import os
import random
import tkinter as tk
from tkinter import font
from tkinter import filedialog

# Reads a binary file and displays the content as a map with unique colors per value
# offset = 5
start_offset = 0
start_width = 60

# file_path = "/tmp/CursedKingdoms/data/TOWN-A"
file_path = "/tmp/CursedKingdoms/data/Bak/MAP0-1"

value_to_color = {}

map_array = [str]


def read_file_as_map(file_path):
    global map_array
    with open(file_path, 'rb') as file:
        byte_pairs = file.read()

    map_array = check_byte_pair([hex(byte_pair)[2:].upper().zfill(2) for byte_pair in byte_pairs])

    # return [f'{byte_pairs[i+1]:02X}' for i in range(0, len(byte_pairs), 2)]


def generate_random_color():
    return f'#{random.randint(0, 0xFFFFFF):06x}'


def check_byte_pair(map_array_):
    for i, value in enumerate(map_array_):
        if i % 2 == 0:
            if value != '00':
                break

    filtered_array = []
    for i, value in enumerate(map_array_):
        if i % 2 == 1:
            filtered_array.append(value)

    return filtered_array


def set_colors():
    unique_values = list(set(map_array))
    return {value: generate_random_color() for value in unique_values}


def draw_map(canvas, row_width, cell_size, offset):
    rows = [map_array[i:i+row_width] for i in range(offset, len(map_array), row_width)]

    canvas_height = len(rows) * cell_size  # Calculate the required canvas height

    canvas.config(scrollregion=(0, 0, cell_size * row_width, canvas_height))  # Set the scrollable region

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


def redraw_map(canvas, row_width_var, cell_size_var, offset_var):
    try:
        row_width = int(row_width_var.get())
        cell_size = int(cell_size_var.get())
        if row_width > 0 and cell_size > 0:
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


def open_file_and_read():
    global file_path
    initial_dir = os.path.dirname(file_path) if file_path else None
    file_dialog = filedialog.Open(filetypes=[("All Files", "*")], initialdir=initial_dir)
    file_path = file_dialog.show()
    if file_path:
        read_file_as_map(file_path)


def create_map_window(offset=0, row_width=16, cell_size=20):
    window = tk.Tk()
    window.title('Map Data')

    frame = tk.Frame(window)
    frame.pack(fill=tk.BOTH, expand=True)

    # Open button

    open_button = tk.Button(frame, text="Open File", command=lambda: (open_file_and_read(), redraw_map(canvas, row_width_var, cell_size_var, offset_var)))
    open_button.grid(row=0, column=0, columnspan=2, sticky='w')  # Place the button in the second row, spanning 2 columns

    # Row_width

    row_width_label = tk.Label(frame, text="Row Width:")
    row_width_label.grid(row=0, column=2, sticky='w')  # Stick to the left side

    row_width_var = tk.StringVar(value=row_width)
    row_width_entry = tk.Entry(frame, textvariable=row_width_var, width=5)  # Adjust the width of the entry field

    row_width_entry.grid(row=0, column=3, sticky='w')

    up_button = tk.Button(frame, text="▲", command=lambda: (increase_row_width(row_width_var), redraw_map(canvas, row_width_var, cell_size_var, offset_var)))
    down_button = tk.Button(frame, text="▼", command=lambda: (decrease_row_width(row_width_var), redraw_map(canvas, row_width_var, cell_size_var, offset_var)))
    up_button.grid(row=0, column=4, sticky='w')
    down_button.grid(row=0, column=5, sticky='w')

    # Offset

    offset_label = tk.Label(frame, text="Offset:")
    offset_label.grid(row=0, column=6, sticky='w')  # Stick to the left side

    offset_var = tk.StringVar(value=offset)
    offset_entry = tk.Entry(frame, textvariable=offset_var, width=5)  # Adjust the width of the entry field
    offset_entry.grid(row=0, column=7, sticky='w')

    # Cell_size

    cell_size_label = tk.Label(frame, text="Cell Size:")
    cell_size_label.grid(row=0, column=8, sticky='w')  # Stick to the left side

    cell_size_var = tk.StringVar(value=cell_size)
    cell_size_entry = tk.Entry(frame, textvariable=cell_size_var, width=5)  # Adjust the width of the entry field
    cell_size_entry.grid(row=0, column=9, sticky='w')

    # Redraw button

    redraw_button = tk.Button(frame, text="Redraw Map", command=lambda: redraw_map(canvas, row_width_var, cell_size_var, offset_var))
    redraw_button.grid(row=0, column=10, columnspan=2, sticky='w')  # Place the button in the second row, spanning 2 columns

    # Canvas

    canvas = tk.Canvas(frame, width=cell_size * row_width, height=1000)  # Adjust the canvas size as needed
    canvas.grid(row=1, column=0, columnspan=11, sticky='w')  # Place canvas in the first row, spanning 3 columns

    # Create a vertical scrollbar
    scrollbar = tk.Scrollbar(frame, command=canvas.yview)
    scrollbar.grid(row=1, column=11, sticky='ns')  # Stick to the north and south

    canvas.config(yscrollcommand=scrollbar.set)  # Connect the scrollbar to the canvas

    # Draw map initially
    draw_map(canvas, row_width, cell_size, offset)

    window.mainloop()


if __name__ == "__main__":
    read_file_as_map(file_path)
    value_to_color = set_colors()
    create_map_window(start_offset, start_width)
