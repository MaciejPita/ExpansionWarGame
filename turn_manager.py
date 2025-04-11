from PyQt5.QtCore import QTimer, pyqtSignal, QObject

class TurnManager(QObject):
    turn_changed = pyqtSignal(str, int)  # color, turn number

    def __init__(self, duration=10000):
        super().__init__()
        self.players = ["green", "red"]
        self.current_index = 0
        self.turn_timer = QTimer()
        self.turn_timer.setInterval(duration)
        self.turn_timer.timeout.connect(self.end_turn_by_timer)
        self.turn_number = 1
        self.turn_active = False

    def start(self):
        self.turn_active = True
        self.turn_timer.start()
        self.turn_changed.emit(self.current_player(), self.turn_number)

    def current_player(self):
        return self.players[self.current_index]

    def end_turn_by_timer(self):
        self.end_turn()

    def end_turn(self):
        self.turn_timer.stop()
        self.current_index = (self.current_index + 1) % len(self.players)
        self.turn_number += 1
        self.turn_active = True
        self.turn_timer.start()
        self.turn_changed.emit(self.current_player(), self.turn_number)

    def stop(self):
        self.turn_timer.stop()
