from PyQt5.QtCore import QTimer, pyqtSignal, QObject
import json
import threading
from PyQt5.QtCore import QMetaObject, Q_ARG, Qt
from PyQt5.QtCore import pyqtSlot

class NetworkTurnManager(QObject):
    turn_changed = pyqtSignal(str, int)  # color, turn number
    remote_move_received = pyqtSignal(dict)  # {"from": [x, y], "to": [x, y]}

    def __init__(self, network, is_host, duration=10000):
        super().__init__()
        self.players = ["green", "red"]
        self.is_host = is_host
        self.my_color = "green" if is_host else "red"
        self.network = network  # instance of Server or Client
        self.turn_timer = QTimer()
        self.turn_timer.setInterval(duration)
        self.turn_timer.timeout.connect(self.end_turn_by_timer)
        self.turn_number = 1
        self.turn_active = False
        self.lock = threading.Lock()

        threading.Thread(target=self.listen_for_moves, daemon=True).start()

    def start(self):
        if self.current_player() == self.my_color:
            self.turn_active = True
            self.turn_timer.start()
            self.turn_changed.emit(self.current_player(), self.turn_number)

    def current_player(self):
        return self.players[(self.turn_number - 1) % len(self.players)]

    def end_turn_by_timer(self):
        self.end_turn()

    def send_move(self, move_data):
        try:
            self.network.send(json.dumps(move_data))
            print(f"[NETWORK] Wysłano ruch: {move_data}")
            self.end_turn()
        except Exception as e:
            print(f"[ERROR] Błąd przy wysyłaniu ruchu: {e}")

    def end_turn(self):
        self.turn_timer.stop()
        self.turn_active = False
        self.turn_number += 1
        self.turn_changed.emit(self.current_player(), self.turn_number)
        if self.current_player() == self.my_color:
            self.turn_timer.start()
            self.turn_active = True

    def listen_for_moves(self):
        while True:
            try:
                data = self.network.receive_data()
                move_data = json.loads(data)
                print(f"[NETWORK] Otrzymano dane: {move_data}")

                if move_data.get("action") == "connect":
                    # Zamiast emitować sygnał od razu robimy bo neida sie gui edytowac z innego watku niz glowny
                    QMetaObject.invokeMethod(self, "_emit_remote_move", Qt.QueuedConnection, Q_ARG(dict, move_data))
                    QTimer.singleShot(0, self.end_turn)  # WAŻNE: też w GUI
                else:
                    print(f"[WARNING] Nieznana akcja: {move_data.get('action')}")
            except Exception as e:
                print(f"[ERROR] Błąd odbioru danych: {e}")

    @pyqtSlot(dict)
    def _emit_remote_move(self, move_data):
        self.remote_move_received.emit(move_data)


