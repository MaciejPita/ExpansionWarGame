from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout, QMainWindow, QPushButton
from game_view import GameView
from levels import LEVELS


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cell Expansion War")
        self.setFixedSize(1044, 828)
        self.show_level_selector()

    def show_level_selector(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # background
        bg_label = QLabel()
        pixmap = QPixmap(":/images/background.png")
        bg_label.setPixmap(pixmap)
        bg_label.setScaledContents(True)
        bg_label.setGeometry(self.rect())

        # buttons
        button_container = QWidget()
        button_layout = QVBoxLayout()
        button_layout.setContentsMargins(30, 30, 30, 30)
        button_layout.setSpacing(20)
        button_container.setLayout(button_layout)
        button_container.setStyleSheet("""
            background-color: rgba(255, 255, 255, 160);
            border-radius: 20px;
        """)

        # tittle
        title = QLabel("Wybierz poziom:")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2e2e2e;
            margin-bottom: 20px;
        """)
        button_layout.addWidget(title)

        button_style = """
            QPushButton {
                background-color: rgba(255, 255, 255, 180);
                border: 2px solid #4CAF50;
                color: #2e2e2e;
                padding: 10px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 12px;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: rgba(76, 175, 80, 200);
                color: white;
            }
            QPushButton:pressed {
                background-color: rgba(56, 142, 60, 220);
            }
        """

        for name in LEVELS:
            btn = QPushButton(name)
            btn.setStyleSheet(button_style)
            btn.setFixedHeight(45)
            btn.clicked.connect(lambda checked, lvl=name: self.start_game(lvl))
            button_layout.addWidget(btn)

        layout.addWidget(button_container)

        stacked_layout = QVBoxLayout(widget)
        stacked_layout.setContentsMargins(0, 0, 0, 0)
        stacked_layout.addWidget(bg_label)
        stacked_layout.addLayout(layout)

        widget.setLayout(stacked_layout)
        self.setCentralWidget(widget)

    def start_game(self, level_name):
        game_view = GameView(level_data=LEVELS[level_name], level_name=level_name, main_window=self)
        self.setCentralWidget(game_view)