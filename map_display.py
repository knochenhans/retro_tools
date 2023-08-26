import copy
from enum import Enum, auto
import os
import random
import shutil
import sys
import tempfile
from typing import Optional
from PySide6 import QtWidgets, QtCore, QtGui
from PIL import Image
import PySide6.QtCore
import PySide6.QtWidgets
import numpy as np

start_offset = 0
start_width = 60

file_path = os.path.dirname(os.path.realpath(__file__)) + "/data/CursedKingdoms/gfx/ALSEND1DATA"  # Replace with the actual file path


class DisplayMode(Enum):
    HEX = auto()
    BIT = auto()
    PALETTE = auto()


value_to_color = {}


class MapDisplay(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.binary_loader = BinaryLoader(self)

        self.str_map_array = [str]
        self.byte_map_buffer = b''

        self.current_width = 0
        self.row_width_edit: QtWidgets.QLineEdit | None = None
        self.cell_size_edit: QtWidgets.QLineEdit | None = None
        self.offset_edit: QtWidgets.QLineEdit | None = None
        self.limit_edit: QtWidgets.QLineEdit | None = None
        self.view: QtWidgets.QGraphicsView | None = None
        self.filter_leading_byte_pair_cb: QtWidgets.QCheckBox | None = None
        self.palette_rows_combo: QtWidgets.QComboBox | None = None

        self.display_mode = DisplayMode.HEX

        # Create a menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('File')
        edit_menu = menu_bar.addMenu('Edit')

        open_action = QtGui.QAction('Open', self)
        open_action.setShortcut(QtGui.QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_file_and_read)

        quit_action = QtGui.QAction('Quit', self)
        quit_action.setShortcut(QtGui.QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)

        dump_selection_action = QtGui.QAction('Dump Selection', self)
        dump_selection_action.setShortcut(QtGui.QKeySequence.StandardKey.Save)
        dump_selection_action.triggered.connect(self.dump_selection)

        file_menu.addAction(open_action)
        file_menu.addAction(quit_action)

        edit_menu.addAction(dump_selection_action)

        self.read_map(file_path)
        self.create_map_view(start_offset, start_width)

        self.selection = (0, len(self.str_map_array))

    def read_file_as_map(self, file_path, preserve_byte_map=True):
        with open(file_path, 'rb') as file:
            byte_map_buffer = file.read()

        if preserve_byte_map:
            self.byte_map_buffer = byte_map_buffer

        return [hex(byte_pair)[2:].upper().zfill(2) for byte_pair in byte_map_buffer]

    def read_map(self, file_path):
        self.str_map_array = self.read_file_as_map(file_path)

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
            except ValueError as e:
                print(e)

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
            self.read_map(file_path)
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

    def erase_noncontinuous_values(self, data, min_occurrence):
        data_list = []

        start_idx = None
        count = 0

        for idx, value in enumerate(data):
            if value[0] == '0':
                if start_idx is None:
                    start_idx = idx
                count += 1
            else:
                if start_idx is not None and count >= min_occurrence:
                    data_list.append((start_idx, idx - 1))
                start_idx = None
                count = 0

        if start_idx is not None and count >= min_occurrence:
            data_list.append((start_idx, len(data) - 1))

        result = ['0000'] * len(data)

        for start, end in data_list:
            result[start:end+1] = data[start:end+1]

        return result

    def select_area(self, start, stop):
        if self.view:
            self.view.scene().clearSelection()
            for item in self.view.scene().items():
                if isinstance(item, ClickableRectItem):
                    if item.file_pos >= start and item.file_pos <= stop:
                        item.setSelected(True)

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
                        # cell_size_mult = 0.5
                        rows = [''.join(filtered_map[i:i + 2]) for i in range(offset, len(filtered_map) - limit_diff, 2)]
                        rows = self.erase_noncontinuous_values(rows, int(self.palette_rows_combo.currentText()))
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
                                bg_color = self.binary_loader.amiga_color_to_rgb(text)
                            else:
                                bg_color = QtGui.QColor(0, 0, 0)

                    x1 = col_index * cell_size * cell_size_mult + counter_text_width
                    y1 = row_index * cell_size * cell_size_mult

                    rect_item = ClickableRectItem(x1, y1, cell_size * cell_size_mult, cell_size * cell_size_mult, row_index * row_width + col_index, self)
                    rect_item.setBrush(bg_color)

                    scene.addItem(rect_item)

                    # Text

                    match self.display_mode:
                        case DisplayMode.HEX:
                            text_item = QtWidgets.QGraphicsSimpleTextItem(text)

                            text_item.setFont(font)
                            text_item.setPos(x1 + cell_size // 2 - text_item.boundingRect().width() // 2, y1 + cell_size // 2 - text_item.boundingRect().height() // 2)
                            scene.addItem(text_item)
                        case DisplayMode.PALETTE:
                            text_item = QtWidgets.QGraphicsSimpleTextItem(text)

                            font.setPointSize(cell_size // 3)

                            text_item.setFont(font)
                            text_item.setPos(x1 + cell_size // 2 - text_item.boundingRect().width() // 2, y1 + cell_size // 2 - text_item.boundingRect().height() // 2)
                            text_item.setBrush(QtGui.QColor(255, 255, 255))
                            scene.addItem(text_item)

                # Add row counter
                text_item = QtWidgets.QGraphicsSimpleTextItem(str(row_index * row_width))
                text_item.setFont(counter_font)
                text_item.setPos(0, y1 + cell_size // 3 - text_item.boundingRect().height() // 3)
                text_item.setBrush(QtGui.QColor(255, 255, 255))

                scene.addItem(text_item)

            self.view.setSceneRect(0, 0, cell_size * row_width, self.canvas_height)  # Set the scene rectangle
            self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)  # Show the vertical scrollbar

    def create_map_view(self, offset=0, row_width=16, cell_size=20):
        self.setGeometry(100, 100, 800, 600)

        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        layout = QtWidgets.QVBoxLayout()
        central_widget.setLayout(layout)

        row_layout = QtWidgets.QHBoxLayout()

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
        merge_button.clicked.connect(lambda: self.merge_bitplanes())

        self.limit_edit.installEventFilter(self)
        self.row_width_edit.installEventFilter(self)
        self.offset_edit.installEventFilter(self)

        # Add all layouts to the main layout
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
        self.palette_rows_combo.currentIndexChanged.connect(self.redraw_map)

        row_layout.addWidget(self.palette_rows_combo)
        row_layout.addWidget(redraw_button)
        row_layout.addWidget(dump_button)
        row_layout.addWidget(merge_button)

        self.selection_label1 = QtWidgets.QLabel('Sel.:')
        self.selection_label2 = QtWidgets.QLabel('0 - 0')
        row_layout.addWidget(self.selection_label1)
        row_layout.addWidget(self.selection_label2)

        layout.addLayout(row_layout)

        # self.canvas
        scene = QtWidgets.QGraphicsScene()
        self.view = QtWidgets.QGraphicsView(scene)
        self.view.setScene(scene)

        layout.addWidget(self.view)

        # Draw map initially
        self.draw_map(row_width, cell_size, offset)

        self.show()

    def merge_bitplanes(self):
        global file_path

        byte_map_buffer = copy.copy(self.byte_map_buffer)

        if len(byte_map_buffer) % 5 != 0:
            error_message = 'The length of the bytearray must be divisible by 5 to split it into 5 equal pieces.'
            QtWidgets.QMessageBox.critical(self, 'Error', error_message)
        else:
            self.image_dialog = ImageDisplay(self.byte_map_buffer)
            self.image_dialog.exec()

    def on_filter_leading_byte_pair_cb(self, state):
        self.redraw_map()

    def set_max_limit(self):
        self.limit_edit.setText(str(len(self.str_map_array)))
        self.redraw_map()

    def on_display_mode_change(self):
        # Slot method to handle display mode change
        if self.bit_radio.isChecked():
            self.display_mode = DisplayMode.BIT

        elif self.hex_radio.isChecked():
            self.display_mode = DisplayMode.HEX

        elif self.palette_radio.isChecked():
            self.display_mode = DisplayMode.PALETTE
        self.redraw_map()

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
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Settings', '/tmp/dump.txt', 'Text Files (*.txt);;All Files (*)')

        if file_name:
            try:
                with open(file_name, 'w', encoding='utf-8') as file:
                    dump = ''
                    dump += f'Width: {self.row_width_edit.text()}\n'
                    dump += f'Offset: {self.offset_edit.text()}'
                    file.write(dump)
            except Exception as e:
                print(f'Error while saving file: {e}')

    def dump_selection(self):
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Selection', '/tmp/dump_selection', 'All Files (*)')

        if file_name:
            start, stop = self.selection

            mult = 1

            match self.display_mode:
                case DisplayMode.HEX:
                    pass
                case DisplayMode.BIT:
                    pass
                case DisplayMode.PALETTE:
                    mult = 2

            binary_data = bytes.fromhex(''.join(self.str_map_array[start * mult:(stop + 1) * mult]))

            # Write bytes to the binary file
            with open(file_name, 'wb') as file:
                file.write(binary_data)


class BinaryLoader():
    def __init__(self, parent):
        self.byte_map_buffer = []
        self.parent = parent

    def read_file_as_map(self, file_path, preserve_byte_map=True):
        with open(file_path, 'rb') as file:
            byte_map_buffer = file.read()

        if preserve_byte_map:
            self.byte_map_buffer = byte_map_buffer

        return [hex(byte_pair)[2:].upper().zfill(2) for byte_pair in byte_map_buffer]

    def open_palette(self):
        initial_dir = os.path.dirname(file_path) if file_path else None
        palette_file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self.parent, 'Open Palette Dump', dir=initial_dir)

        if palette_file_path:
            palette_data = self.read_file_as_map(palette_file_path, preserve_byte_map=False)
            return [''.join(palette_data[i:i + 2]) for i in range(0, len(palette_data), 2)]
        return []

    def palette_to_rgb(self, palette):
        rgb_colors = []

        for color in palette:
            q_color = self.amiga_color_to_rgb(color)
            rgb_colors.append((q_color.red(), q_color.green(), q_color.blue()))
        return rgb_colors

    def amiga_color_to_rgb(self, text):
        text_expanded = ''.join([c * 2 for c in text])
        red = int(text_expanded[2:4], 16)
        green = int(text_expanded[4:6], 16)
        blue = int(text_expanded[6:], 16)
        bg_color = QtGui.QColor.fromRgb(red, green, blue)
        return bg_color


class ImageDisplay(QtWidgets.QDialog):
    def __init__(self, byte_map_buffer, parent=None) -> None:
        super().__init__(parent)

        self.binary_loader = BinaryLoader(self)
        self.byte_map_buffer = byte_map_buffer

        layout = QtWidgets.QVBoxLayout()
        button_layout = QtWidgets.QHBoxLayout()

        self.image_path = ""

        self.pixmap = QtGui.QPixmap(320, 200)
        self.pixmap.fill(QtGui.QColor(0, 0, 0))
        self.label = QtWidgets.QLabel(self)
        self.label.setPixmap(self.pixmap)
        layout.addWidget(self.label)

        save_button = QtWidgets.QPushButton('Save', self)
        save_button.clicked.connect(self.save_merged_image)
        button_layout.addWidget(save_button)

        palette_button = QtWidgets.QPushButton('Load New Palette', self)
        palette_button.clicked.connect(self.load_palette)
        button_layout.addWidget(palette_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.tmp_image = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        self.load_palette()

    def load_palette(self):
        from bitplanelib import bitplanes_raw2image

        palette = self.binary_loader.open_palette()
        rgb_colors = self.binary_loader.palette_to_rgb(palette)

        bitplanes_raw2image(self.byte_map_buffer, 5, 320, 200, self.tmp_image.name, rgb_colors)
        self.pixmap.load(self.tmp_image.name)
        self.label.setPixmap(self.pixmap)

    def save_merged_image(self):
        global file_path
        initial_dir = os.path.dirname(file_path) if file_path else None
        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Merged Data as PNG', dir=initial_dir, filter='PNG Files (*.png)')

        if save_path:
            if not save_path.lower().endswith('.png'):
                save_path += '.png'

                shutil.move(self.image_path, save_path)

                self.tmp_image.close()
                self.close()


class ClickableRectItem(QtWidgets.QGraphicsRectItem):
    def __init__(self, x, y, width, height, file_pos, map_display: MapDisplay):
        super().__init__(x, y, width, height)
        self.setBrush(QtGui.Qt.GlobalColor.white)
        self.setPen(QtGui.Qt.PenStyle.NoPen)
        self.setAcceptHoverEvents(True)  # Enable hover events
        self.setFlags(QtWidgets.QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable)  # Enable selection

        self.file_pos = file_pos
        self.map_display = map_display

    def mousePressEvent(self, event):
        if event.button() == QtGui.Qt.MouseButton.LeftButton:
            self.scene().clearSelection()
            self.setSelected(True)

            start, stop = self.map_display.selection
            if event.modifiers() == QtGui.Qt.KeyboardModifier.NoModifier:
                start = self.file_pos
                stop = start
                self.map_display.selection = (start, stop)
                # self.map_display.selection = (self.file_pos, self.file_pos)
            elif event.modifiers() == QtGui.Qt.KeyboardModifier.ShiftModifier:
                new_stop = self.file_pos
                if new_stop < start:  # Switch values if new_stop is less than start
                    start, stop = new_stop, start
                else:
                    stop = new_stop
                self.map_display.select_area(start, stop)
                self.map_display.selection = (start, stop)
            elif event.modifiers() == QtGui.Qt.KeyboardModifier.AltModifier:
                start = self.file_pos
                stop = start + int(self.map_display.palette_rows_combo.currentText()) - 1
                self.map_display.select_area(start, stop)
                self.map_display.selection = (start, stop)
            else:
                super().mousePressEvent(event)

            start, stop = self.map_display.selection
            self.map_display.selection_label2.setText(f'{start} - {stop} ({stop-start+1})')

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == QtGui.Qt.MouseButton.LeftButton:
            if event.modifiers() == QtGui.Qt.KeyboardModifier.ShiftModifier or event.modifiers() == QtGui.Qt.KeyboardModifier.AltModifier:
                pass
            else:
                return super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        multiple = False

        items = self.scene().selectedItems()
        if len(self.scene().selectedItems()) > 0:
            if self in items:
                multiple = True

        menu = QtWidgets.QMenu()

        if multiple:
            action1 = menu.addAction('Dump selection')
            action = menu.exec(event.screenPos())

            if action == action1:
                self.map_display.dump_selection()
        else:
            pass


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    start_offset = 0
    start_width = 16

    map_display = MapDisplay()

    map_display.show()
    sys.exit(app.exec())
