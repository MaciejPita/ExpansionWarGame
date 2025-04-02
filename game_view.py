import logging
import random
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtCore import QPointF, QTimer
from PyQt5.QtGui import QPixmap, QBrush, QColor, QPainter
from PyQt5.QtWidgets import QLabel, QGraphicsPixmapItem, QHBoxLayout, QWidget, QPushButton, QGraphicsView, \
    QGraphicsScene, QVBoxLayout, QGraphicsItem
from nodes import BaseNode, ConnectionLine, PreviewLine, HintLine



class GameEndOverlay(QGraphicsItem):
    def __init__(self, message, color, is_win=True, confetti=True):
        super().__init__()
        self.message = message
        self.text_color = color
        self.confetti_enabled = confetti
        self.is_win = is_win
        self.opacity = 0.0
        self.confetti_particles = []
        self.setZValue(100)

        self.timer = QTimer()
        self.timer.timeout.connect(self.fade_in)
        self.timer.start(40)

    def boundingRect(self):
        return QRectF(0, 0, 1024, 768)

    def paint(self, painter, option, widget=None):
        if self.opacity <= 0.0:
            return

        painter.setRenderHint(QPainter.Antialiasing)

        bg = QColor(0, 0, 0, int(180 * self.opacity)) if not self.is_win else QColor(255, 255, 255, int(100 * self.opacity))
        painter.fillRect(self.boundingRect(), bg)

        font = painter.font()
        font.setPointSize(48)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(self.text_color.lighter(120))
        painter.drawText(self.boundingRect(), Qt.AlignCenter, self.message)

        if self.confetti_enabled:
            for particle in self.confetti_particles:
                if not particle["pos"].isNull():
                    painter.setBrush(particle['color'])
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(particle['pos'], 6, 6)

    def fade_in(self):
        if self.opacity < 1.0:
            self.opacity += 0.05
            if self.confetti_enabled:
                self.spawn_confetti()
            self.update()
        else:
            self.timer.stop()

    def spawn_confetti(self):
        if len(self.confetti_particles) >= 100:
            return
        for _ in range(6):
            self.confetti_particles.append({
                'pos': QPointF(random.randint(0, 1024), random.randint(0, 768)),
                'color': QColor(random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
            })

class GameView(QGraphicsView):
    def __init__(self, level_data, level_name, main_window):
        self.logger = logging.getLogger("WojnaEkspansji")
        self.logger.info(f"Inicjalizacja GameView dla poziomu: {level_name}")
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.NoDrag)

        self.nodes = []
        self.selected_node = None
        self.level_data = level_data
        self.level_name = level_name
        self.main_window = main_window
        self.create_scene()

        self.ai_timer = QTimer()
        self.ai_timer.timeout.connect(self.enemy_ai_turn)
        self.ai_timer.start(3000)

        self.hint_line = None

        self.preview_lines = []
        self.preview_visible = False

        self.round_time_seconds = 120  # 2 minuty
        self.round_timer = QTimer()
        self.round_timer.timeout.connect(self.update_round_timer)
        self.round_timer.start(1000)

        self.round_label = QLabel()
        self.round_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(0, 0, 0, 100);
                font-size: 16px;
                padding: 6px;
                border-radius: 8px;
            }
        """)
        self.round_label.setText("Pozostały czas: 2:00")

        self.round_proxy = self.scene.addWidget(self.round_label)
        self.round_proxy.setZValue(10)
        self.update_round_label_position()

        self.flash_timer = QTimer()
        self.flash_timer.timeout.connect(self.flash_round_label)
        self.flash_on = False  # stan migania

        self.node_placement_used = False  # gracz może tylko raz dodać węzeł

    def update_round_timer(self):
        self.round_time_seconds -= 1
        minutes = self.round_time_seconds // 60
        seconds = self.round_time_seconds % 60
        self.round_label.setText(f"Pozostały czas: {minutes}:{seconds:02}")

        if self.round_time_seconds <= 10:
            if not self.flash_timer.isActive():
                self.flash_timer.start(500)  # migaj co 0.5s

        if self.round_time_seconds <= 0:
            self.round_timer.stop()
            self.flash_timer.stop()
            self.show_end_message("Przegrana", "Czas się skończył!")

    def flash_round_label(self):
        self.flash_on = not self.flash_on
        if self.flash_on:
            self.round_label.setStyleSheet("""
                QLabel {
                    color: red;
                    background-color: rgba(0, 0, 0, 160);
                    font-size: 16px;
                    padding: 6px;
                    border-radius: 8px;
                }
            """)
        else:
            self.round_label.setStyleSheet("""
                QLabel {
                    color: white;
                    background-color: rgba(0, 0, 0, 100);
                    font-size: 16px;
                    padding: 6px;
                    border-radius: 8px;
                }
            """)

    def check_game_over(self):

        green_nodes = [n for n in self.nodes if n.is_player]
        red_nodes = [n for n in self.nodes if not n.is_player]

        if not green_nodes:
            self.show_end_message("Przegrałeś")
        elif not red_nodes:
            self.show_end_message("Wygrałeś")

    def show_end_message(self, title, message):
        self.round_timer.stop()
        self.ai_timer.stop()
        self.flash_timer.stop()
        for node in self.nodes:
            node.production_timer.stop()

        is_win = (title == "Wygrana")
        color = QColor("green") if is_win else QColor("red")

        self.overlay_ref = GameEndOverlay(message, color)
        self.scene.addItem(self.overlay_ref)

        # Bezpieczny powrót do menu
        if hasattr(self, "main_window") and self.main_window and hasattr(self.main_window, "show_level_selector"):
            QTimer.singleShot(6000, self.main_window.show_level_selector)
        else:
            print("Brak main_window – nie można wrócić do menu.")

    def enemy_ai_turn(self):
        red_nodes = [node for node in self.nodes if node.color_name == "red"]
        green_nodes = [node for node in self.nodes if node.color_name == "green"]

        if not red_nodes or not green_nodes:
            return

        for red_node in red_nodes:
            if red_node.unit_count < 2:
                continue  # Zbyt mało jednostek, nie atakuje

            # Szukaj najsłabszego zielonego węzła słabszego od czerwonego
            weak_targets = [g for g in green_nodes if g.unit_count < red_node.unit_count]

            if not weak_targets:
                # Brak słabszych celów – czekamy i "ładujemy" węzeł (czyli nic nie robimy)
                continue

            # Wybierz najsłabszy z możliwych celów
            target = min(weak_targets, key=lambda g: g.unit_count)

            # Stwórz połączenie ataku
            if red_node.can_connect() and target.can_connect():
                line = ConnectionLine(red_node, target, self.scene)
                self.scene.addItem(line)
                red_node.register_connection()
        self.check_game_over()

    def create_scene(self):
        self.setSceneRect(0, 0, 1024, 768)
        self.setFixedSize(1040, 788)

        bg_pixmap = QPixmap(":/images/background.png")
        if not bg_pixmap.isNull():
            self.scene.setBackgroundBrush(QBrush(bg_pixmap))

        self.nodes = []
        for node_info in self.level_data:
            node = BaseNode(
                x=node_info["x"],
                y=node_info["y"],
                radius=30,
                color=node_info["color"],
                is_player=(node_info["color"] == "green"),
                initial_units=node_info["units"],
                node_type=node_info["type"],
                max_connections=node_info.get("max_connections", 3)  # domyślnie 3
            )

            self.nodes.append(node)
            self.scene.addItem(node)

        # Dodaj przyciski
        self.add_menu_buttons()

    def add_menu_buttons(self):
        self.menu_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        button_style = """
            QPushButton {
                background-color: rgba(255, 255, 255, 180);
                border: 2px solid #4CAF50;
                color: #2e2e2e;
                padding: 6px 12px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 10px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: rgba(76, 175, 80, 200);
                color: white;
            }
            QPushButton:pressed {
                background-color: rgba(56, 142, 60, 220);
            }
        """

        btn_restart = QPushButton("🔄 Restart")
        btn_restart.setStyleSheet(button_style)
        btn_restart.clicked.connect(lambda: self.main_window.start_game(self.level_name))

        btn_back = QPushButton("⬅ Menu")
        btn_back.setStyleSheet(button_style)
        btn_back.clicked.connect(self.main_window.show_level_selector)

        layout.addWidget(btn_restart)
        layout.addWidget(btn_back)
        self.menu_widget.setLayout(layout)
        self.menu_widget.setStyleSheet("background-color: rgba(255, 255, 255, 80); border-radius: 12px;")

        proxy = self.scene.addWidget(self.menu_widget)
        proxy.setZValue(10)

        # Połącz z aktualizacją pozycji – wywołaj teraz i przy każdym resize
        self.menu_proxy = proxy
        self.update_menu_position()

        btn_hint = QPushButton("💡 Podpowiedź")
        btn_hint.setStyleSheet(button_style)
        btn_hint.clicked.connect(self.show_ai_hint)
        layout.addWidget(btn_hint)

        # MENU DODAWANIA WĘZŁA
        self.node_selection_widget = QWidget()
        node_layout = QHBoxLayout()
        node_layout.setContentsMargins(5, 5, 5, 5)
        node_layout.setSpacing(10)

        for node_type in ["circle", "plus", "triangle"]:
            pixmap = QPixmap(f":/images/green_{'node' if node_type == 'circle' else node_type}.png").scaled(48, 48,
                                                                                                            Qt.KeepAspectRatio,
                                                                                                            Qt.SmoothTransformation)
            label = DraggableLabel(pixmap, node_type, self)
            node_layout.addWidget(label)

        self.node_selection_widget.setLayout(node_layout)
        self.node_selection_proxy = self.scene.addWidget(self.node_selection_widget)
        self.node_selection_proxy.setZValue(10)
        self.update_node_menu_position()

    def start_drag_node(self, node_type, pixmap):
        if self.node_placement_used:
            return

        self.drag_node_type = node_type
        self.drag_node_pixmap = pixmap
        self.drag_node_item = QGraphicsPixmapItem(pixmap)
        self.drag_node_item.setOpacity(0.7)
        self.scene.addItem(self.drag_node_item)

        self.setCursor(Qt.ClosedHandCursor)
        self.setMouseTracking(True)

    def update_node_menu_position(self):
        if hasattr(self, 'node_selection_proxy'):
            view_width = self.viewport().width()
            view_height = self.viewport().height()
            menu_size = self.node_selection_widget.sizeHint()
            margin = 10
            x = (view_width - menu_size.width()) / 2
            y = view_height - menu_size.height() - margin
            self.node_selection_proxy.setPos(x, y)

    def show_ai_hint(self):
        if self.hint_line:
            self.scene.removeItem(self.hint_line)
            self.hint_line = None


        green_nodes = [n for n in self.nodes if n.color_name == "green"]
        red_nodes = [n for n in self.nodes if n.color_name == "red"]
        all_nodes = self.nodes

        if not green_nodes or not red_nodes:
            return

        # Analiza dominacji
        dominance = len(green_nodes) - len(red_nodes)  # >0 = przewaga gracza

        best_score = float('-inf')
        best_pair = None

        for source in green_nodes:
            if not source.can_connect() or source.unit_count < 2:
                continue

            for target in all_nodes:
                if source == target:
                    continue
                if target.current_connections >= target.max_connections:
                    continue

                distance = (source.pos() - target.pos()).manhattanLength()

                score = 0
                action_type = None

                if target.color_name == "red":
                    if target.unit_count >= source.unit_count:
                        continue  # nie atakuj silniejszych

                    # Bazowa ocena ataku
                    score += (source.unit_count - target.unit_count) * 10

                    # Karanie za odległość
                    score -= distance * 0.2

                    # Priorytet dla node'ów plus
                    if target.node_type == "plus":
                        score += 20

                    # Premia za bliskość innych zielonych
                    allies_near = [a for a in green_nodes if (a.pos() - target.pos()).manhattanLength() < 150]
                    score += len(allies_near) * 5

                    action_type = "attack"

                elif target.color_name == "green":
                    if target.unit_count >= source.unit_count:
                        continue

                    # Bazowa ocena wsparcia
                    score += (source.unit_count - target.unit_count) * 3
                    score -= distance * 0.1

                    # Jeśli w pobliżu są wrogowie – zwiększ priorytet
                    enemies_near = [e for e in red_nodes if (e.pos() - target.pos()).manhattanLength() < 200]
                    if enemies_near and target.unit_count < 6:
                        score += 15

                    action_type = "support"

                else:
                    continue  # nieistotne

                # Zachowanie zależne od dominacji
                if dominance < 0 and action_type == "support":
                    score += 10  # gracz w defensywie – wspieraj

                if dominance > 2 and action_type == "attack":
                    score += 10  # gracz dominuje – atakuj więcej

                if score > best_score:
                    best_score = score
                    best_pair = (source, target)

        if best_pair:
            source, target = best_pair
            self.hint_line = HintLine(source, target)
            self.scene.addItem(self.hint_line)
            self.pulsing_node = target
            target.start_pulsing()
            QTimer.singleShot(5000, self.stop_hint_animation)

            # Automatyczne usunięcie po 5 sekundach
            QTimer.singleShot(5000, self.remove_hint_line)

    class DraggableLabel(QLabel):
        def __init__(self, pixmap, node_type, parent_view):
            super().__init__()
            self.setPixmap(pixmap)
            self.node_type = node_type
            self.parent_view = parent_view
            self.setCursor(Qt.OpenHandCursor)
            self.setFixedSize(pixmap.size())
            self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        def mousePressEvent(self, event):
            self.parent_view.start_drag_node(self.node_type, self.pixmap())

    def remove_hint_line(self):
        if self.hint_line:
            self.scene.removeItem(self.hint_line)
            self.hint_line = None

    def update_menu_position(self):
        if hasattr(self, 'menu_proxy'):
            view_width = self.viewport().width()
            menu_size = self.menu_widget.sizeHint()
            margin = 0
            x = view_width - menu_size.width() - margin
            y = margin
            self.menu_proxy.setPos(x, y)

    def show_possible_moves(self, source_node):
        self.clear_preview_lines()

        if not source_node.can_connect():
            return

        for target in self.nodes:
            if target == source_node:
                continue
            if target.current_connections >= target.max_connections:
                continue

            # Dodaj tylko jeśli jeszcze niepołączone i nieprzekroczono limitów
            line = PreviewLine(source_node, target)
            self.scene.addItem(line)
            self.preview_lines.append(line)

    def clear_preview_lines(self):
        for line in self.preview_lines:
            self.scene.removeItem(line)
        self.preview_lines.clear()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_menu_position()
        self.update_round_label_position()
        self.update_node_menu_position()

    def update_round_label_position(self):
        if hasattr(self, 'round_proxy'):
            view_width = self.viewport().width()
            view_height = self.viewport().height()
            label_size = self.round_label.sizeHint()
            margin = 10
            x = view_width - label_size.width() - margin
            y = view_height - label_size.height() - margin
            self.round_proxy.setPos(x, y)

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        while item and not isinstance(item, BaseNode):
            item = item.parentItem()

        if isinstance(item, BaseNode) and item.is_player:
            self.selected_node = item
        else:
            self.selected_node = None

        super().mousePressEvent(event)



    def mouseMoveEvent(self, event):
        if hasattr(self, 'drag_node_item') and self.drag_node_item:
            scene_pos = self.mapToScene(event.pos())
            self.drag_node_item.setPos(scene_pos - QPointF(24, 24))  # Wycentrowanie
        super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.pos())
        while item and not isinstance(item, BaseNode):
            item = item.parentItem()

        if isinstance(item, BaseNode) and item.is_player:
            if self.preview_visible:
                self.clear_preview_lines()
                self.selected_node = None
                self.preview_visible = False
            else:
                self.selected_node = item
                self.show_possible_moves(item)
                self.preview_visible = True
        else:
            self.clear_preview_lines()
            self.selected_node = None
            self.preview_visible = False

        super().mouseDoubleClickEvent(event)

    def mouseReleaseEvent(self, event):
        if self.selected_node:
            target_item = self.itemAt(event.pos())
            if isinstance(target_item, BaseNode) and target_item != self.selected_node:
                if self.selected_node.can_connect() and target_item.can_connect():
                    line = ConnectionLine(self.selected_node, target_item, self.scene)
                    self.scene.addItem(line)
                    self.selected_node.register_connection()
            self.selected_node.register_connection()
            self.check_game_over()

        self.selected_node = None
        super().mouseReleaseEvent(event)

        if hasattr(self, 'drag_node_item') and self.drag_node_item:
            scene_pos = self.mapToScene(event.pos())
            valid = True

            for node in self.nodes:
                if (node.pos() - scene_pos).manhattanLength() < 70:
                    valid = False
                    break

            if valid:
                new_node = BaseNode(
                    x=scene_pos.x(), y=scene_pos.y(),
                    radius=30, color="green",
                    is_player=True, initial_units=8,
                    node_type=self.drag_node_type, max_connections=3
                )
                self.scene.addItem(new_node)
                self.nodes.append(new_node)
                self.node_placement_used = True

            self.scene.removeItem(self.drag_node_item)
            del self.drag_node_item
            self.setCursor(Qt.ArrowCursor)

    def stop_hint_animation(self):
        if self.hint_line:
            self.scene.removeItem(self.hint_line)
            self.hint_line = None

        if self.pulsing_node:
            self.pulsing_node.stop_pulsing()
            self.pulsing_node = None


class DraggableLabel(QLabel):
    def __init__(self, pixmap, node_type, parent_view):
        super().__init__()
        self.setPixmap(pixmap)
        self.node_type = node_type
        self.parent_view = parent_view
        self.setCursor(Qt.OpenHandCursor)
        self.setFixedSize(pixmap.size())
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

    def mousePressEvent(self, event):
        self.parent_view.start_drag_node(self.node_type, self.pixmap())
