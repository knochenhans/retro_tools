from enum import Enum, auto
import os
import random
import sys
from PySide6 import QtWidgets, QtCore, QtGui
from PIL import Image
import numpy as np


# Reads a binary file and displays the content as a map with unique colors per value
# offset = 5
start_offset = 0
start_width = 60

# file_path = "/tmp/CursedKingdoms/data/TOWN-A"
# file_path = "/tmp/CursedKingdoms/data/MAP0-0"
# file_path = "/tmp/bitplane_output"
file_path = os.path.dirname(os.path.realpath(__file__)) + "/data/CursedKingdoms/gfx/ALSEND1DATA"  # Replace with the actual file path


class DisplayMode(Enum):
    HEX = auto()
    BIT = auto()
    PALETTE = auto()


value_to_color = {}


class MapDisplay(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.str_map_array = [str]

        self.byte_map = b''

        self.current_width = 0
        self.row_width_edit: QtWidgets.QLineEdit | None = None
        self.cell_size_edit: QtWidgets.QLineEdit | None = None
        self.offset_edit: QtWidgets.QLineEdit | None = None
        self.limit_edit: QtWidgets.QLineEdit | None = None
        self.view: QtWidgets.QGraphicsView | None = None
        self.filter_leading_byte_pair_cb: QtWidgets.QCheckBox | None = None
        self.palette_rows_combo: QtWidgets.QComboBox | None = None

        self.display_mode = DisplayMode.HEX

    def read_file_as_map(self, file_path):
        global value_to_color
        with open(file_path, 'rb') as file:
            self.byte_map = file.read()

        self.str_map_array = [hex(byte_pair)[2:].upper().zfill(2) for byte_pair in self.byte_map]

        self.set_colors()

        filename = os.path.basename(file_path)
        self.setWindowTitle(f'Map Data - {filename}')

    def generate_random_color(self):
        red = random.randint(0, 255)
        green = random.randint(0, 255)
        blue = random.randint(0, 255)

        # Create a QColor object with the random RGB values
        color = QtGui.QColor(red, green, blue)

        return color

    def filter_map(self):
        filtered_array = []
        for i, value in enumerate(self.str_map_array):
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
        unique_values = list(set(self.str_map_array))

        for value in unique_values:
            if value not in value_to_color:
                value_to_color[value] = self.generate_random_color()

    def redraw_map(self):
        if self.row_width_edit and self.cell_size_edit and self.offset_edit and self.view:
            try:
                row_width = int(self.row_width_edit.text())
                cell_size = int(self.cell_size_edit.text())
                if row_width > 0 and cell_size > 0:
                    offset = int(self.offset_edit.text())
                    self.view.scene().clear()  # Clear the self.canvas
                    self.draw_map(row_width, cell_size, offset)
            except ValueError:
                pass

    def increase_row_width(self):
        if self.row_width_edit:
            try:
                self.current_width = int(self.row_width_edit.text())
                self.row_width_edit.setText(str(self.current_width + 1))
                self.redraw_map()
            except ValueError:
                pass

    def decrease_row_width(self):
        if self.row_width_edit:
            try:
                self.current_width = int(self.row_width_edit.text())
                if self.current_width > 1:
                    self.row_width_edit.setText(str(self.current_width - 1))
                self.redraw_map()
            except ValueError:
                pass

    def open_file_and_read(self):
        global file_path
        initial_dir = os.path.dirname(file_path) if file_path else None
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", dir=initial_dir)
        if file_path:
            self.read_file_as_map(file_path)
            self.limit_edit.setText(str(len(self.str_map_array)))

            filter = True
            for i, value in enumerate(self.str_map_array):
                if i % 2 == 0:
                    if value != '00':
                        filter = False
                        break
            if filter:
                self.filter_leading_byte_pair_cb.setChecked(True)
                print('Filtering out leading zero byte pairs')
                self.filter_map()

            self.redraw_map()

    def hex_to_binary(self, hex_string):
        decimal_value = int(hex_string, 16)
        binary_string = format(decimal_value, '08b')  # '08b' formats the integer as an 8-bit binary string
        return list(binary_string)

    def find_continuous_lines(self, data, min_occurrences=2):
        if not data:
            return []

        current_start = -1
        output = []

        for i, element in enumerate(data):
            if element[0] == '0':
                if current_start == -1:
                    current_start = i
            else:
                if (i - current_start) >= min_occurrences:
                    output += data[current_start:i]
                    output.append('0000')
                else:
                    for j in range(i - current_start):
                        output.append('0000')
                current_start = -1

        if current_start != -1:  # Handle the last continuous line
            output += data[current_start:]

        return output

        # continuous_lines = []
        # current_line = []

        # for element in data:
        #     if element.startswith(start_value):
        #         current_line.append(element)
        #     else:
        #         if len(current_line) >= min_occurrences:
        #             continuous_lines.append(current_line)
        #         current_line = []

        # if len(current_line) >= min_occurrences:
        #     continuous_lines.append(current_line)

        # return continuous_lines

    def draw_map(self, row_width, cell_size, offset):
        if self.view:
            limit_diff = 0
            limit = len(self.str_map_array)

            if self.limit_edit:
                limit = int(self.limit_edit.text())

                if limit != 0:
                    limit_diff = len(self.str_map_array) - limit

            filtered_map = self.str_map_array

            if self.filter_leading_byte_pair_cb.isChecked():
                filtered_map = self.filter_map()

            cell_size_mult = 1.0

            if self.palette_rows_combo:
                match self.display_mode:
                    case DisplayMode.HEX:
                        rows = [filtered_map[i:i + row_width] for i in range(offset, len(filtered_map) - limit_diff, row_width)]
                    case DisplayMode.BIT:
                        cell_size_mult = 0.2
                        expanded_bits = [bit for hex_value in filtered_map[:limit] for bit in self.hex_to_binary(hex_value)]
                        rows = [expanded_bits[i:i + row_width] for i in range(offset, len(expanded_bits), row_width)]
                    case DisplayMode.PALETTE:
                        cell_size_mult = 0.5
                        rows = [''.join(filtered_map[i:i + 2]) for i in range(offset, len(filtered_map) - limit_diff, 2)]
                        rows = self.find_continuous_lines(rows, int(self.palette_rows_combo.currentText()))
                        rows = [rows[i:i + row_width] for i in range(0, len(rows), row_width)]

                self.canvas_height = len(rows) * cell_size * cell_size_mult  # Calculate the required self.canvas height

            scene = QtWidgets.QGraphicsScene()
            self.view.setScene(scene)

            font = QtGui.QFont()
            font.setFamily('Courier New')
            font.setPointSize(cell_size // 1.5)

            counter_font = QtGui.QFont()
            # counter_font.setFamily('Courier New')
            counter_font.setPointSize(cell_size // 3)

            counter_text_width = 50

            for row_index, row in enumerate(rows):
                y1 = 0

                for col_index, element in enumerate(row):
                    text = str(element)

                    match self.display_mode:
                        case DisplayMode.HEX:
                            bg_color = value_to_color.get(text, QtGui.QColor(0, 0, 0))
                        case DisplayMode.BIT:
                            if text == '0':
                                bg_color = QtGui.QColor(0, 0, 0)
                            else:
                                bg_color = QtGui.QColor(255, 255, 255)
                        case DisplayMode.PALETTE:
                            if text[0] == '0':
                                text_expanded = ''.join([c * 2 for c in text])
                                red = int(text_expanded[2:4], 16)
                                green = int(text_expanded[4:6], 16)
                                blue = int(text_expanded[6:], 16)
                                bg_color = QtGui.QColor.fromRgb(red, green, blue)
                            else:
                                bg_color = QtGui.QColor(0, 0, 0)

                    x1 = col_index * cell_size * cell_size_mult + counter_text_width
                    y1 = row_index * cell_size * cell_size_mult
                    # x2 = x1 + cell_size
                    # y2 = y1 + cell_size

                    rect_item = QtWidgets.QGraphicsRectItem(x1, y1, cell_size * cell_size_mult, cell_size * cell_size_mult)
                    rect_item.setBrush(QtCore.Qt.GlobalColor.white)  # Set the default background color
                    rect_item.setPen(QtCore.Qt.PenStyle.NoPen)  # Remove the border

                    rect_item.setBrush(bg_color)

                    scene.addItem(rect_item)

                    match self.display_mode:
                        case DisplayMode.HEX:
                            text_item = QtWidgets.QGraphicsSimpleTextItem(text)

                            text_item.setFont(font)
                            text_item.setPos(x1 + cell_size // 2 - text_item.boundingRect().width() // 2, y1 + cell_size // 2 - text_item.boundingRect().height() // 2)
                            scene.addItem(text_item)
                        case DisplayMode.PALETTE:
                            pass

                # Add row counter
                text_item = QtWidgets.QGraphicsSimpleTextItem(str(row_index * row_width))
                text_item.setFont(counter_font)
                text_item.setPos(0, y1 + cell_size // 3 - text_item.boundingRect().height() // 3)
                text_item.setBrush(QtGui.QColor(255, 255, 255))

                scene.addItem(text_item)

            self.view.setSceneRect(0, 0, cell_size * row_width, self.canvas_height)  # Set the scene rectangle
            self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)  # Show the vertical scrollbar

    def create_map_window(self, offset=0, row_width=16, cell_size=20, limit=0):
        self.setGeometry(100, 100, 800, 600)

        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        layout = QtWidgets.QVBoxLayout()
        central_widget.setLayout(layout)

        row_layout = QtWidgets.QHBoxLayout()

        # Open button
        open_button = QtWidgets.QPushButton('Open File')
        open_button.clicked.connect(lambda: (self.open_file_and_read()))

        # Row Width
        row_width_layout = QtWidgets.QHBoxLayout()
        row_width_label = QtWidgets.QLabel('Row Width:')
        self.row_width_edit = QtWidgets.QLineEdit(str(row_width))
        row_width_layout.addWidget(row_width_label)
        row_width_layout.addWidget(self.row_width_edit)

        # Offset
        offset_layout = QtWidgets.QHBoxLayout()
        offset_label = QtWidgets.QLabel('Offset:')
        self.offset_edit = QtWidgets.QLineEdit(str(offset))
        offset_layout.addWidget(offset_label)
        offset_layout.addWidget(self.offset_edit)

        # Limit
        limit_layout = QtWidgets.QHBoxLayout()
        limit_label = QtWidgets.QLabel('Limit:')
        self.limit_edit = QtWidgets.QLineEdit(str(len(self.str_map_array)))
        limit_layout.addWidget(limit_label)
        limit_layout.addWidget(self.limit_edit)

        # Max limit button
        max_limit_button = QtWidgets.QPushButton('Max')
        max_limit_button.clicked.connect(lambda: self.set_max_limit())

        # Cell Size
        cell_size_layout = QtWidgets.QHBoxLayout()
        cell_size_label = QtWidgets.QLabel('Cell Size:')
        self.cell_size_edit = QtWidgets.QLineEdit(str(cell_size))
        cell_size_layout.addWidget(cell_size_label)
        cell_size_layout.addWidget(self.cell_size_edit)

        # Filter out leading zero byte pair
        self.filter_leading_byte_pair_cb = QtWidgets.QCheckBox('Filter leading 00')
        self.filter_leading_byte_pair_cb.setChecked(False)
        self.filter_leading_byte_pair_cb.stateChanged.connect(self.on_filter_leading_byte_pair_cb)
        self.filter_leading_byte_pair_label = QtWidgets.QLabel('Filter leading 00')

        filter_leading_byte_pair_layout = QtWidgets.QHBoxLayout()
        filter_leading_byte_pair_layout.addWidget(self.filter_leading_byte_pair_cb)
        filter_leading_byte_pair_layout.addWidget(self.filter_leading_byte_pair_label)

        # Redraw button
        redraw_button = QtWidgets.QPushButton('Redraw Map')
        redraw_button.clicked.connect(lambda: self.redraw_map())

        # Dump
        dump_button = QtWidgets.QPushButton('Dump')
        dump_button.clicked.connect(lambda: self.dump())

        # Merge
        merge_button = QtWidgets.QPushButton('Merge')
        merge_button.clicked.connect(lambda: self.merge())

        self.limit_edit.installEventFilter(self)
        self.row_width_edit.installEventFilter(self)
        self.offset_edit.installEventFilter(self)

        # Add all layouts to the main layout
        row_layout.addWidget(open_button)
        row_layout.addLayout(row_width_layout)
        row_layout.addLayout(offset_layout)
        row_layout.addLayout(limit_layout)
        row_layout.addWidget(max_limit_button)
        row_layout.addLayout(cell_size_layout)
        row_layout.addLayout(filter_leading_byte_pair_layout)

        # Display Mode Radio Buttons
        mode_layout = QtWidgets.QHBoxLayout()
        self.display_mode_label = QtWidgets.QLabel('Display Mode:')
        self.bit_radio = QtWidgets.QRadioButton('Bit')
        self.hex_radio = QtWidgets.QRadioButton('Hex')
        self.palette_radio = QtWidgets.QRadioButton('Palette')

        if self.display_mode == DisplayMode.HEX:
            self.hex_radio.setChecked(True)
        else:
            self.bit_radio.setChecked(True)

        # Connect the radio buttons' toggled signals to a slot method
        self.bit_radio.toggled.connect(self.on_display_mode_change)
        self.hex_radio.toggled.connect(self.on_display_mode_change)
        self.palette_radio.toggled.connect(self.on_display_mode_change)

        mode_layout.addWidget(self.display_mode_label)
        mode_layout.addWidget(self.bit_radio)
        mode_layout.addWidget(self.hex_radio)
        mode_layout.addWidget(self.palette_radio)

        row_layout.addLayout(mode_layout)

        self.palette_rows_combo = QtWidgets.QComboBox()
        self.palette_rows_combo.addItems(['8', '16', '32'])
        self.palette_rows_combo.setCurrentIndex(self.palette_rows_combo.findText('32'))

        row_layout.addWidget(self.palette_rows_combo)
        row_layout.addWidget(redraw_button)
        row_layout.addWidget(dump_button)
        row_layout.addWidget(merge_button)

        layout.addLayout(row_layout)

        # self.canvas
        scene = QtWidgets.QGraphicsScene()
        self.view = QtWidgets.QGraphicsView(scene)
        self.view.setScene(scene)

        layout.addWidget(self.view)

        # Draw map initially
        self.draw_map(row_width, cell_size, offset)

        # Set up the key press event for the main window
        self.window.keyPressEvent = self.on_key_press

        self.window.show()

    def merge(self):
        from bitplanelib import bitplanes_raw2image

        if len(self.byte_map) % 5 != 0:
            raise ValueError("The length of the bytearray must be divisible by 5 to split it into 5 equal pieces.")

        piece_size = len(self.byte_map) // 5
        bitplanes = [self.byte_map[i * piece_size: (i + 1) * piece_size] for i in range(5)]

        palette = [(0, 0, 0),        # Black
                   (48, 48, 48),     # Dark Gray
                   (64, 64, 64),     # Gray
                   (96, 0, 0),       # Dark Red
                   (160, 0, 0),      # Red
                   (209, 1, 0),      # Scarlet Red
                   (0, 0, 0),        # Black (repeated)
                   (48, 48, 48),     # Dark Gray (repeated)
                   (64, 64, 64),     # Gray (repeated)
                   (96, 0, 0),       # Dark Red (repeated)
                   (160, 0, 0),      # Red (repeated)
                   (209, 1, 0),      # Scarlet Red (repeated)
                   (0, 0, 0),        # Black (repeated)
                   (48, 48, 48),     # Dark Gray (repeated)
                   (64, 64, 64),     # Gray (repeated)
                   (96, 0, 0),       # Dark Red (repeated)
                   (160, 0, 0),      # Red (repeated)
                   (209, 1, 0),      # Scarlet Red (repeated)
                   (0, 0, 0),        # Black (repeated)
                   (48, 48, 48),     # Dark Gray (repeated)
                   (64, 64, 64),     # Gray (repeated)
                   (96, 0, 0),       # Dark Red (repeated)
                   (160, 0, 0),      # Red (repeated)
                   (209, 1, 0),      # Scarlet Red (repeated)
                   (0, 0, 0),        # Black (repeated)
                   (48, 48, 48),     # Dark Gray (repeated)
                   (64, 64, 64),     # Gray (repeated)
                   (96, 0, 0),       # Dark Red (repeated)
                   (160, 0, 0),      # Red (repeated)
                   (209, 1, 0),       # Scarlet Red (repeated)
                   (48, 48, 48),     # Dark Gray (repeated)
                   (64, 64, 64),     # Gray (repeated)
                   (96, 0, 0),       # Dark Red (repeated)
                   (160, 0, 0),      # Red (repeated)
                   (209, 1, 0)       # Scarlet Red (repeated)
                   ]

        bitplanes_raw2image(self.byte_map, 5, 320, 200, '/tmp/test.png', palette)
        # chunky_row = []

        # startx = 0
        # starty = 32
        # width = 5
        # height = 5

        # for x in range((starty * width), width * height + (starty * width)):
        #     pixel_value = 0
        #     for bitplane_index in range(len(bitplanes)):
        #         bit_value = (bitplanes[bitplane_index][x // 8] >> (7 - (x & 7) % 8)) & 1
        #         pixel_value |= bit_value
        #         if bitplane_index < 4:
        #             pixel_value <<= 1
        #     # if x % 2 == 1:
        #     #     chunky_row.append((buffer<<4) | (pixel_value>>4))
        #     # else:
        #     #     buffer = pixel_value

        #     chunky_row.append(pixel_value)

        # pixels = []

        # for y in range(width):
        #     row = []
        #     for x in range(height):
        #         row.append(palette[chunky_row[x + y]])
        #     pixels.append(row)

        # # Convert the pixels into an array using numpy
        # array = np.array(pixels, dtype=np.uint8)

        # # image = Image.frombytes('1', (320, 200), bitplanes[0])
        # # image = Image.frombytes('1', (320, 200), chunky_row)
        # # image = image.convert('L')

        # image = Image.fromarray(array)

        # image.show()

    def on_filter_leading_byte_pair_cb(self, state):
        self.redraw_map()

    def set_max_limit(self):
        self.limit_edit.setText(str(len(self.str_map_array)))
        self.redraw_map()

    def on_display_mode_change(self):
        # Slot method to handle display mode change
        if self.bit_radio.isChecked():
            self.display_mode = DisplayMode.BIT
            self.redraw_map()

        elif self.hex_radio.isChecked():
            self.display_mode = DisplayMode.HEX
            self.redraw_map()

        elif self.palette_radio.isChecked():
            self.display_mode = DisplayMode.PALETTE
            self.redraw_map()

    def on_key_press(self, event):
        if event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier and event.key() == QtCore.Qt.Key.Key_O:
            self.open_file_and_read()

    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.Type.KeyPress:
            key = event.key()
            redraw = False

            if key == QtCore.Qt.Key.Key_Up or key == QtCore.Qt.Key.Key_Down:
                def modify_value(value, increment, decrement, multiplier):
                    if event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier and key == increment:
                        value *= multiplier
                    elif key == increment:
                        value += 1
                    elif event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier and key == decrement:
                        value //= multiplier
                    elif event.modifiers() == QtCore.Qt.KeyboardModifier.ShiftModifier and key == increment:
                        value += 10
                    elif event.modifiers() == QtCore.Qt.KeyboardModifier.ShiftModifier and key == decrement:
                        value -= 10
                    elif key == decrement:
                        if value > 0:
                            value -= 1
                    return value

                if source == self.row_width_edit:
                    current_row_width = int(self.row_width_edit.text())
                    current_row_width = modify_value(current_row_width, QtCore.Qt.Key.Key_Up, QtCore.Qt.Key.Key_Down, 2)
                    self.row_width_edit.setText(str(current_row_width))
                    redraw = True

                elif source == self.limit_edit:
                    current_limit = int(self.limit_edit.text())
                    current_limit = modify_value(current_limit, QtCore.Qt.Key.Key_Up, QtCore.Qt.Key.Key_Down, 2)
                    self.limit_edit.setText(str(current_limit))
                    redraw = True

                elif source == self.offset_edit:
                    current_offset = int(self.offset_edit.text())
                    current_offset = modify_value(current_offset, QtCore.Qt.Key.Key_Up, QtCore.Qt.Key.Key_Down, 2)
                    self.offset_edit.setText(str(current_offset))
                    redraw = True

                if redraw:
                    self.redraw_map()
                    return True

        return super().eventFilter(source, event)

    def dump(self):
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Settings Dump', '/tmp/dump.txt', 'Text Files (*.txt);;All Files (*)')

        if file_name:
            try:
                with open(file_name, 'w', encoding='utf-8') as file:
                    dump = ''
                    dump += f'Width: {self.row_width_edit.text()}\n'
                    dump += f'Offset: {self.offset_edit.text()}'
                    file.write(dump)
            except Exception as e:
                print(f'Error while saving file: {e}')


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    start_offset = 0
    start_width = 16

    map_display = MapDisplay()

    map_display.show()
    sys.exit(app.exec())
