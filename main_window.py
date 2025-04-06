from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtGui import QPixmap, QRegExpValidator
from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout, QMainWindow, QPushButton, QButtonGroup, QRadioButton, \
    QHBoxLayout, QLineEdit, QTextEdit
from pymongo import MongoClient
import json
import os

from game_view import GameView
from levels import LEVELS
from mongo_client import game_history_collection


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cell Expansion War")
        self.setFixedSize(1044, 828)
        self.setStyleSheet("""
            QMainWindow {
                background-image: url(:/images/background.png);
                background-repeat: no-repeat;
                background-position: center;
            }
        """)
        self.last_level_name = None
        self.selected_game_mode = "1 gracz"
        self.show_level_selector()

    def update_game_mode(self):
        if self.mode_single.isChecked():
            self.selected_game_mode = "1 gracz"
        elif self.mode_local.isChecked():
            self.selected_game_mode = "2 graczy lokalnie"
        elif self.mode_online.isChecked():
            self.selected_game_mode = "Gra sieciowa"

    def show_level_selector(self):
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(50)
        layout.setAlignment(Qt.AlignCenter)

        # Tryb gry (lewa kolumna)
        mode_layout = QVBoxLayout()
        mode_layout.setAlignment(Qt.AlignTop)

        mode_container = QWidget()
        mode_container_layout = QVBoxLayout()
        mode_container_layout.setContentsMargins(30, 30, 30, 30)
        mode_container_layout.setSpacing(15)

        mode_container.setLayout(mode_container_layout)
        mode_container.setStyleSheet("""
            background-color: rgba(255, 255, 255, 160);
            border-radius: 20px;
        """)

        mode_label = QLabel("Tryb gry:")
        mode_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #2e2e2e;")
        mode_label.setAlignment(Qt.AlignCenter)

        self.mode_group = QButtonGroup(self)

        self.mode_single = QRadioButton("1 gracz \U0001F3AE")
        self.mode_local = QRadioButton("2 graczy lokalnie \U0001F46B")
        self.mode_online = QRadioButton("Gra sieciowa \U0001F310")

        self.mode_single.setChecked(True)

        for btn in [self.mode_single, self.mode_local, self.mode_online]:
            btn.setStyleSheet("""
                QRadioButton { font-size: 16px; color: #2e2e2e; }
                QRadioButton::indicator { width: 18px; height: 18px; }
            """)
            self.mode_group.addButton(btn)
            btn.toggled.connect(self.update_game_mode)  # <-- Kluczowa linia

        mode_container_layout.addWidget(mode_label)
        mode_container_layout.addSpacing(10)
        mode_container_layout.addWidget(self.mode_single)
        mode_container_layout.addWidget(self.mode_local)
        mode_container_layout.addWidget(self.mode_online)

        self.ip_input = IPPortInput()
        mode_container_layout.addWidget(self.ip_input)

        mode_container_layout.addStretch()

        # Historia przyciski
        button_style = """
            QPushButton {
                background-color: rgba(255, 255, 255, 180);
                border: 2px solid #4CAF50;
                color: #2e2e2e;
                padding: 8px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: rgba(76, 175, 80, 200);
                color: white;
            }
            QPushButton:pressed {
                background-color: rgba(56, 142, 60, 220);
            }
        """

        btn_show_xml = QPushButton("\U0001F4C2 Zobacz zapis historii")
        btn_show_xml.setStyleSheet(button_style)
        btn_show_xml.clicked.connect(self.show_history_xml)

        btn_nosql = QPushButton("\u2601 Zobacz zapis historii (MongoDB)")
        btn_nosql.setStyleSheet(button_style)
        btn_nosql.clicked.connect(self.show_history_mongodb)

        btn_json = QPushButton("\U0001F4DD Zobacz zapis historii (JSON)")
        btn_json.setStyleSheet(button_style)
        btn_json.clicked.connect(self.show_history_json)

        history_buttons = QVBoxLayout()
        history_buttons.setSpacing(8)
        history_buttons.addWidget(btn_show_xml)
        history_buttons.addWidget(btn_nosql)
        history_buttons.addWidget(btn_json)

        history_widget = QWidget()
        history_widget.setLayout(history_buttons)
        mode_container_layout.addWidget(history_widget)

        mode_layout.addWidget(mode_container)

        # Poziomy (prawa kolumna)
        level_layout = QVBoxLayout()
        level_layout.setAlignment(Qt.AlignTop)

        button_container = QWidget()
        button_layout = QVBoxLayout()
        button_layout.setContentsMargins(30, 30, 30, 30)
        button_layout.setSpacing(20)
        button_container.setLayout(button_layout)
        button_container.setStyleSheet("""
            background-color: rgba(255, 255, 255, 160);
            border-radius: 20px;
        """)

        title = QLabel("Wybierz poziom:")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2e2e2e; margin-bottom: 20px;")
        button_layout.addWidget(title)

        for name in LEVELS:
            btn = QPushButton(name)
            btn.setStyleSheet(button_style.replace("13px", "16px"))
            btn.setFixedHeight(45)
            btn.clicked.connect(lambda checked, lvl=name: self.start_game(lvl))
            button_layout.addWidget(btn)

        level_layout.addWidget(button_container)

        layout.addLayout(mode_layout)
        layout.addLayout(level_layout)

        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def show_history_xml(self):
        self._display_text_history(f"historia_{self.last_level_name}.xml", "📖 Historia gry")

    def show_history_mongodb(self):
        try:
            last_entry = game_history_collection.find().sort("_id", -1).limit(1)[0]
            content = json.dumps(last_entry, indent=4, default=str)
            self._display_text_history(text=content, title="☁ Historia z MongoDB")
        except Exception as e:
            self._display_text_history(text=f"Błąd: {e}", title="☁ Historia z MongoDB")

    def show_history_json(self):
        if not os.path.exists("historia.json"):
            self._display_text_history(text="Nie znaleziono pliku historia.json", title="📝 Historia gry (JSON)")
            return
        with open("historia.json", "r", encoding="utf-8") as f:
            content = json.load(f)
        pretty = json.dumps(content, indent=4, ensure_ascii=False)
        self._display_text_history(text=pretty, title="📝 Historia gry (JSON)")

    def _display_text_history(self, filename=None, text=None, title="Historia"):
        container = QWidget()
        layout = QVBoxLayout()
        label = QLabel(title)
        layout.addWidget(label)

        view = QTextEdit()
        view.setReadOnly(True)
        view.setStyleSheet("font-family: Consolas; font-size: 14px;")

        if filename and os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                view.setText(f.read())
        elif text:
            view.setText(text)
        else:
            view.setText("Brak danych do wyświetlenia")

        layout.addWidget(view)

        btn_back = QPushButton("⬅ Powrót do menu")
        btn_back.clicked.connect(self.show_level_selector)
        layout.addWidget(btn_back)

        container.setLayout(layout)
        self.setCentralWidget(container)

    def start_game(self, level_name):
        if self.selected_game_mode == "1 gracz":
            level_data = LEVELS[level_name]
            self.game_view = GameView(level_data, level_name, self, mode="single")
            self.last_level_name = level_name
            self.setCentralWidget(self.game_view)
        elif self.selected_game_mode == "2 graczy lokalnie":
            label = QLabel("Tryb lokalny niezaimplementowany.")
            container = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(label)
            container.setLayout(layout)
            self.setCentralWidget(container)
        elif self.selected_game_mode == "Gra sieciowa":
            label = QLabel(f"\u0141\u0105cz\u0119 si\u0119 z: {self.ip_input.get_value()}")
            container = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(label)
            container.setLayout(layout)
            self.setCentralWidget(container)


class IPPortInput(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()
        self.setLayout(layout)

        label = QLabel("Adres IP i port:")
        self.input = QLineEdit()
        self.input.setPlaceholderText("Np. 127.0.0.1:12345")

        ip_port_regex = QRegExp(r"^(\d{1,3}\.){3}\d{1,3}:\d{1,5}$")
        validator = QRegExpValidator(ip_port_regex, self.input)
        self.input.setValidator(validator)

        layout.addWidget(label)
        layout.addWidget(self.input)

    def get_value(self):
        return self.input.text()

    def is_valid(self):
        return self.input.hasAcceptableInput()
