import os
import random
import sys
from PySide6 import QtWidgets, QtCore, QtGui

# Reads a binary file and displays the content as a map with unique colors per value
# offset = 5
start_offset = 0
start_width = 60

# file_path = "/tmp/CursedKingdoms/data/TOWN-A"
# file_path = "/tmp/CursedKingdoms/data/MAP0-0"
# file_path = "/tmp/bitplane_output"
file_path = os.path.dirname(os.path.realpath(__file__)) + "/data/Hanger/Pics/Scanner.Pak"  # Replace with the actual file path


value_to_color = {}

map_array = [str]


class MapDisplay(QtWidgets.QApplication):
    def __init__(self):
        super().__init__()
        self.window = QtWidgets.QMainWindow()
        self.current_width = 0
        self.row_width_var: QtWidgets.QLineEdit | None = None
        self.cell_size_var: QtWidgets.QLineEdit | None = None
        self.offset_var: QtWidgets.QLineEdit | None = None
        self.canvas: QtWidgets.QGraphicsView | None = None

    def read_file_as_map(self, file_path):
        global map_array, value_to_color, window
        with open(file_path, 'rb') as file:
            byte_pairs = file.read()

        map_array = self.check_byte_pair([hex(byte_pair)[2:].upper().zfill(2) for byte_pair in byte_pairs])

        self.set_colors()

        filename = os.path.basename(file_path)
        self.window.setWindowTitle(f'Map Data - {filename}')

    def generate_random_color(self):
        red = random.randint(0, 255)
        green = random.randint(0, 255)
        blue = random.randint(0, 255)

        # Create a QColor object with the random RGB values
        color = QtGui.QColor(red, green, blue)

        return color

    def check_byte_pair(self, map_array_):
        for i, value in enumerate(map_array_):
            if i % 2 == 0:
                if value != '00':
                    break

        filtered_array = []
        for i, value in enumerate(map_array_):
            if i % 2 == 1:
                filtered_array.append(value)

        return filtered_array

    # def int_to_qcolor(color_int):
    #     red = color_int // (256 * 256)  # Quotient for red component
    #     green = (color_int // 256) % 256  # Quotient for green component, remainder for blue component
    #     blue = color_int % 256  # Remainder for blue component

    #     return QtGui.QColor.fromHsv(color_int / 65536 * 359, color_int / 65536 * 255, 255)

    # def get_color(hex_string):
    #     # max_hex_values = 65536
    #     # max_rgb_values = 256**3  # The maximum value for each RGB component

    #     # Calculate the RGB value at the current distance
    #     return int_to_qcolor((int(hex_string, 16) + 1) * 255)

    def set_colors(self):
        unique_values = list(set(map_array))

        for value in unique_values:
            if value not in value_to_color:
                value_to_color[value] = self.generate_random_color()

    def redraw_map(self):
        if self.row_width_var and self.cell_size_var and self.offset_var and self.canvas:
            try:
                row_width = int(self.row_width_var.text())
                cell_size = int(self.cell_size_var.text())
                if row_width > 0 and cell_size > 0:
                    offset = int(self.offset_var.text())
                    self.canvas.scene().clear()  # Clear the self.canvas
                    self.draw_map(row_width, cell_size, offset)
            except ValueError:
                pass

    def increase_row_width(self):
        if self.row_width_var:
            try:
                self.current_width = int(self.row_width_var.text())
                self.row_width_var.setText(str(self.current_width + 1))
                self.redraw_map()
            except ValueError:
                pass

    def decrease_row_width(self):
        if self.row_width_var:
            try:
                self.current_width = int(self.row_width_var.text())
                if self.current_width > 1:
                    self.row_width_var.setText(str(self.current_width - 1))
                self.redraw_map()
            except ValueError:
                pass

    def open_file_and_read(self):
        global file_path
        initial_dir = os.path.dirname(file_path) if file_path else None
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self.window, "Open File", dir=initial_dir)
        if file_path:
            self.read_file_as_map(file_path)
            self.redraw_map()

    def draw_map(self, row_width, cell_size, offset):
        if self.canvas:
            rows = [map_array[i:i + row_width] for i in range(offset, len(map_array), row_width)]

            self.canvas_height = len(rows) * cell_size  # Calculate the required self.canvas height

            scene = QtWidgets.QGraphicsScene()
            self.canvas.setScene(scene)

            font = QtGui.QFont()
            font.setFamily('Courier New')
            font.setPointSize(8)

            for row_index, row in enumerate(rows):
                for col_index, element in enumerate(row):
                    text = str(element)
                    bg_color = value_to_color.get(text, QtGui.QColor(0, 0, 0))
                    x1 = col_index * cell_size
                    y1 = row_index * cell_size
                    x2 = x1 + cell_size
                    y2 = y1 + cell_size

                    rect_item = QtWidgets.QGraphicsRectItem(x1, y1, cell_size, cell_size)
                    rect_item.setBrush(QtCore.Qt.GlobalColor.white)  # Set the default background color
                    rect_item.setPen(QtCore.Qt.PenStyle.NoPen)  # Remove the border

                    rect_item.setBrush(bg_color)  # Replace 'red' with the appropriate color based on the value

                    scene.addItem(rect_item)

                    text_item = QtWidgets.QGraphicsSimpleTextItem(text)

                    text_item.setFont(font)
                    text_item.setPos(x1 + cell_size // 2 - text_item.boundingRect().width() // 2, y1 + cell_size // 2 - text_item.boundingRect().height() // 2)
                    scene.addItem(text_item)

            self.canvas.setSceneRect(0, 0, cell_size * row_width, self.canvas_height)  # Set the scene rectangle
            self.canvas.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)  # Show the vertical scrollbar

    def create_map_window(self, offset=0, row_width=16, cell_size=20):
        self.window.setGeometry(100, 100, 800, 600)

        central_widget = QtWidgets.QWidget()
        self.window.setCentralWidget(central_widget)

        layout = QtWidgets.QVBoxLayout()
        central_widget.setLayout(layout)

        row_layout = QtWidgets.QHBoxLayout()

        # Open button
        open_button = QtWidgets.QPushButton('Open File')
        open_button.clicked.connect(lambda: (self.open_file_and_read()))

        # Row Width
        row_width_layout = QtWidgets.QHBoxLayout()
        row_width_label = QtWidgets.QLabel('Row Width:')
        self.row_width_var = QtWidgets.QLineEdit(str(row_width))
        row_width_layout.addWidget(row_width_label)
        row_width_layout.addWidget(self.row_width_var)

        up_button = QtWidgets.QPushButton('▲')
        up_button.clicked.connect(lambda: (self.increase_row_width()))

        down_button = QtWidgets.QPushButton('▼')
        down_button.clicked.connect(lambda: (self.decrease_row_width()))

        row_width_layout.addWidget(up_button)
        row_width_layout.addWidget(down_button)

        # Offset
        offset_layout = QtWidgets.QHBoxLayout()
        offset_label = QtWidgets.QLabel('Offset:')
        self.offset_var = QtWidgets.QLineEdit(str(offset))
        offset_layout.addWidget(offset_label)
        offset_layout.addWidget(self.offset_var)

        # Cell Size
        cell_size_layout = QtWidgets.QHBoxLayout()
        cell_size_label = QtWidgets.QLabel('Cell Size:')
        self.cell_size_var = QtWidgets.QLineEdit(str(cell_size))
        cell_size_layout.addWidget(cell_size_label)
        cell_size_layout.addWidget(self.cell_size_var)

        # Redraw button
        redraw_button = QtWidgets.QPushButton('Redraw Map')
        redraw_button.clicked.connect(lambda: self.redraw_map())

        # Add all layouts to the main layout
        row_layout.addWidget(open_button)
        row_layout.addLayout(row_width_layout)
        row_layout.addLayout(offset_layout)
        row_layout.addLayout(cell_size_layout)
        row_layout.addWidget(redraw_button)

        layout.addLayout(row_layout)

        # self.canvas
        scene = QtWidgets.QGraphicsScene()
        self.canvas = QtWidgets.QGraphicsView(scene)
        self.canvas.setScene(scene)

        # Create a vertical scrollbar
        # scrollbar = QtWidgets.QScrollBar(QtCore.Qt.Orientation.Vertical)
        # scroll_area = QtWidgets.QScrollArea()
        # scroll_area.setWidget(self.canvas)
        # scroll_area.setVerticalScrollBar(scrollbar)

        # layout.addWidget(scroll_area)
        layout.addWidget(self.canvas)

        # Draw map initially
        self.draw_map(row_width, cell_size, offset)

        self.window.show()


if __name__ == '__main__':
    start_offset = 0
    start_width = 16

    map_display = MapDisplay()

    map_display.read_file_as_map(file_path)
    map_display.create_map_window(start_offset, start_width)
    sys.exit(map_display.exec())
