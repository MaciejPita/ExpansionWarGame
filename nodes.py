import random

from PyQt5.QtCore import Qt

from PyQt5.QtCore import QSequentialAnimationGroup, QPropertyAnimation, QPointF, QTimer, QRectF, QLineF
from PyQt5.QtGui import QPainterPath, QPixmap, QPainter, QPen, QBrush, QColor
from PyQt5.QtWidgets import QGraphicsOpacityEffect, QGraphicsItem, QGraphicsEllipseItem, QGraphicsLineItem, \
    QGraphicsScene





class BaseNode(QGraphicsEllipseItem):
    def __init__(self, x, y, radius, color, is_player=False, initial_units=10, node_type="circle", max_connections=3):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)
        self.setBrush(QBrush(QColor(color)))
        self.setPen(QPen(Qt.white, 2))
        self.setPos(x, y)
        self.radius = radius
        self.color_name = color
        self.is_player = is_player
        self.unit_count = initial_units
        self.node_type = node_type
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)

        self.production_timer = QTimer()
        self.production_timer.timeout.connect(self.produce_unit)
        self.production_timer.start(self.production_interval())

        self.max_connections = max_connections
        self.current_connections = 0

    def play_capture_animation(self):
        self.setGraphicsEffect(None)  # Reset jak coś zostało

        effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(effect)

        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(600)
        animation.setStartValue(0.3)
        animation.setKeyValueAt(0.5, 1.0)
        animation.setEndValue(0.3)
        animation.setLoopCount(3)

        # Usunięcie efektu po zakończeniu animacji
        def on_finished():
            self.setGraphicsEffect(None)
            self.update()

        animation.finished.connect(on_finished)

        animation.start()

        self._animation = animation  # zapobiegaj GC

    def can_connect(self):
        return self.current_connections < self.max_connections

    def register_connection(self):
        self.current_connections += 1

    def unregister_connection(self):
        if self.current_connections > 0:
            self.current_connections -= 1

    def production_interval(self):
        # Czas produkcji zależy od typu
        if self.node_type == "plus":
            return 1500  # szybsza produkcja
        elif self.node_type == "triangle":
            return 2500  # wolniejsza
        else:
            return 2000  # domyślna

    def produce_unit(self):
        max_units = 30
        if self.unit_count < max_units:
            self.unit_count += 1
            self.update()

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # Dla typu "circle" używamy "node" w nazwie pliku
        image_name = "node" if self.node_type == "circle" else self.node_type
        pixmap_path = f":/images/{self.color_name}_{image_name}.png"
        pixmap = QPixmap(pixmap_path)

        if not pixmap.isNull():
            size = 60
            scaled = pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(-30, -30, scaled)
        else:
            # fallback jeśli obrazek nie został znaleziony
            painter.setBrush(self.brush())
            painter.setPen(self.pen())

            if self.node_type == "circle":
                painter.drawEllipse(self.boundingRect())
            elif self.node_type == "triangle":
                path = QPainterPath()
                r = self.radius
                path.moveTo(0, -r)
                path.lineTo(r, r)
                path.lineTo(-r, r)
                path.closeSubpath()
                painter.drawPath(path)
            elif self.node_type == "plus":
                path = QPainterPath()
                w = self.radius * 0.4
                h = self.radius * 1.2
                path.addRect(-w / 2, -h / 2, w, h)
                path.addRect(-h / 2, -w / 2, h, w)
                painter.drawPath(path)

        # Rysowanie liczby jednostek
        font = painter.font()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        painter.setPen(Qt.black)

        text = str(self.unit_count)
        rect = self.boundingRect()
        painter.drawText(rect, Qt.AlignCenter, text)

        # Rysowanie kropek połączeń (pod liczbą jednostek)
        dot_radius = 3
        spacing = 10
        total = self.max_connections
        used = self.current_connections
        y_offset = self.boundingRect().center().y() + 12  # nieco poniżej środka

        start_x = -((dot_radius * 2 + spacing) * (total - 1)) / 2

        for i in range(total):
            if i < used:
                painter.setBrush(Qt.black)
            else:
                painter.setBrush(Qt.white)
            painter.setPen(Qt.NoPen)
            x = start_x + i * (dot_radius * 2 + spacing)
            painter.drawEllipse(QPointF(x, y_offset), dot_radius, dot_radius)


    def decrease_unit(self, amount=1):
        self.unit_count = max(0, self.unit_count - amount)
        self.update()

    def start_pulsing(self):
        if hasattr(self, '_pulse_anim'):
            return  # Nie uruchamiaj ponownie jeśli już działa

        self._pulse_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self._pulse_effect)

        pulse_out = QPropertyAnimation(self._pulse_effect, b"opacity")
        pulse_out.setDuration(500)
        pulse_out.setStartValue(1.0)
        pulse_out.setEndValue(0.3)

        pulse_in = QPropertyAnimation(self._pulse_effect, b"opacity")
        pulse_in.setDuration(500)
        pulse_in.setStartValue(0.3)
        pulse_in.setEndValue(1.0)

        self._pulse_anim = QSequentialAnimationGroup()
        self._pulse_anim.addAnimation(pulse_out)
        self._pulse_anim.addAnimation(pulse_in)
        self._pulse_anim.setLoopCount(-1)
        self._pulse_anim.start()

    def stop_pulsing(self):
        if hasattr(self, '_pulse_anim'):
            self._pulse_anim.stop()
            del self._pulse_anim
            self.setGraphicsEffect(None)


class Unit(QGraphicsItem):
    def __init__(self, start_pos: QPointF, end_pos: QPointF, target_node, source_color, source_node_type="circle", color='white', speed=1.5):
        super().__init__()
        self._radius = 5
        self.color = QColor(color)
        self.setPos(start_pos)
        self.target = end_pos
        self.target_node = target_node
        self.source_color = source_color
        self.source_node_type = source_node_type
        self.speed = speed

        self.timer = QTimer()
        self.timer.timeout.connect(self.move_step)
        self.timer.start(16)

    def boundingRect(self) -> QRectF:
        r = self._radius
        return QRectF(-r, -r, 2 * r, 2 * r)

    def paint(self, painter: QPainter, option, widget=None):
        pixmap = QPixmap(":/images/green_unit.png")
        size = 20
        scaled = pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        painter.drawPixmap(-10, -10, scaled)

    def move_step(self):
        current = self.pos()
        direction = self.target - current
        dist = (direction.x() ** 2 + direction.y() ** 2) ** 0.5

        if dist < self.speed:
            self.setPos(self.target)
            self.timer.stop()

            if self.target_node and self.target_node.color_name == self.source_color:
                healing = HealingEffect(self.target, self.scene())
                self.scene().addItem(healing)
            else:
                spark = SparkEffect(self.target, self.scene(), color=QColor(255, 215, 0))
                self.scene().addItem(spark)

            if self.target_node:
                if self.target_node.color_name == self.source_color:
                    # Wysyłanie do swojego — wsparcie
                    if self.source_node_type == "plus":
                        self.target_node.unit_count += 2
                    else:
                        self.target_node.unit_count += 1
                    self.target_node.update()
                else:
                    # Atak na wroga
                    if self.source_node_type == "triangle":
                        self.target_node.decrease_unit(2)
                    else:
                        self.target_node.decrease_unit(1)

                    # Sprawdź, czy przejmujemy
                    if self.target_node.unit_count == 0:
                        self.target_node.color_name = self.source_color
                        self.target_node.is_player = (self.source_color == "green")
                        self.target_node.unit_count = 1
                        self.target_node.current_connections = 0

                        # Usuń stare linie
                        for item in list(self.scene().items()):
                            if isinstance(item, ConnectionLine):
                                if item.start_node == self.target_node or item.end_node == self.target_node:
                                    if item.owner_color == item.start_node.color_name:
                                        item.start_node.unregister_connection()
                                    self.scene().removeItem(item)

                        self.target_node.play_capture_animation()
                        self.target_node.update()
                        # Sprawdź zwycięstwo/przegraną
                        if self.scene():
                            view = self.scene().views()[0]
                            from game_view import GameView
                            if isinstance(view, GameView):
                                view.check_game_over()

            if self.scene():
                self.scene().removeItem(self)
            return

        step = direction / dist * self.speed
        self.setPos(current + step)



class ConnectionLine(QGraphicsLineItem):
    def __init__(self, start_node, end_node, scene):
        super().__init__(QLineF(start_node.pos(), end_node.pos()))
        self.setPen(QPen(QColor("lightgreen"), 3, Qt.DashLine))
        self.start_node = start_node
        self.end_node = end_node
        self.setZValue(-1)

        self.scene_ref = scene
        self.timer = QTimer()
        self.timer.timeout.connect(self.send_unit)
        self.timer.start(1000)

        self.owner_color = start_node.color_name  # zakładamy że start_node to właściciel

    def send_unit(self):
        if self.start_node.unit_count > 0:
            unit = Unit(
                self.start_node.pos(),
                self.end_node.pos(),
                target_node=self.end_node,
                source_color=self.start_node.color_name,
                source_node_type=self.start_node.node_type,
                color='lightgreen'
            )
            self.scene_ref.addItem(unit)
            self.start_node.decrease_unit(1)

    def mousePressEvent(self, event):
        if self.owner_color != "green":
            return  # Gracz może usuwać tylko swoje linie

        self.timer.stop()
        if self.scene():
            if self.owner_color == self.start_node.color_name:
                self.start_node.unregister_connection()

            self.scene().removeItem(self)




class PreviewLine(QGraphicsLineItem):
    def __init__(self, start_node, end_node):
        super().__init__(QLineF(start_node.pos(), end_node.pos()))
        self.setPen(QPen(QColor(0, 255, 0, 80), 2, Qt.DashLine))
        self.setZValue(-4)


class HintLine(QGraphicsLineItem):
    def __init__(self, start_node, end_node):
        super().__init__(QLineF(start_node.pos(), end_node.pos()))
        self.setPen(QPen(QColor(255, 255, 255, 120), 3, Qt.DashDotLine))
        self.setZValue(-5)
        self.start_node = start_node
        self.end_node = end_node

class SparkEffect(QGraphicsItem):
    def __init__(self, position: QPointF, scene: QGraphicsScene, color: QColor = QColor(255, 215, 0)):
        super().__init__()
        self.setPos(position)
        self.frames = 5
        self.current_frame = 0
        self.scene_ref = scene
        self.color = color

        self.timer = QTimer()
        self.timer.timeout.connect(self.advance_frame)
        self.timer.start(50)

        self.radius = 15

    def boundingRect(self) -> QRectF:
        r = self.radius
        return QRectF(-r, -r, 2 * r, 2 * r)

    def paint(self, painter: QPainter, option, widget=None):
        if self.current_frame >= self.frames:
            return
        painter.setRenderHint(QPainter.Antialiasing)
        fading_color = QColor(self.color)
        fading_color.setAlpha(180 - self.current_frame * 30)
        painter.setBrush(fading_color)
        painter.setPen(Qt.NoPen)
        for _ in range(6):
            x = random.randint(-self.radius, self.radius)
            y = random.randint(-self.radius, self.radius)
            painter.drawEllipse(QPointF(x, y), 2, 2)

    def advance_frame(self):
        self.current_frame += 1
        if self.current_frame >= self.frames:
            self.timer.stop()
            if self.scene_ref:
                self.scene_ref.removeItem(self)
        else:
            self.update()


    def boundingRect(self) -> QRectF:
        r = self.radius
        return QRectF(-r, -r, 2 * r, 2 * r)

    def paint(self, painter: QPainter, option, widget=None):
        if self.current_frame >= self.frames:
            return
        painter.setRenderHint(QPainter.Antialiasing)
        color = QColor(255, 215, 0, 180 - self.current_frame * 30)  # Zanikające iskry
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        for _ in range(6):  # 6 iskierek
            x = random.randint(-self.radius, self.radius)
            y = random.randint(-self.radius, self.radius)
            painter.drawEllipse(QPointF(x, y), 2, 2)

    def advance_frame(self):
        self.current_frame += 1
        if self.current_frame >= self.frames:
            self.timer.stop()
            if self.scene_ref:
                self.scene_ref.removeItem(self)
        else:
            self.update()

class HealingEffect(QGraphicsItem):
    def __init__(self, position: QPointF, scene: QGraphicsScene):
        super().__init__()
        self.setPos(position)
        self.scene_ref = scene
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_effect)
        self.timer.start(40)

        self.ring_radius = 5
        self.max_radius = 40
        self.opacity = 1.0

    def boundingRect(self) -> QRectF:
        r = self.max_radius
        return QRectF(-r, -r, 2 * r, 2 * r)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        color = QColor(100, 255, 100, int(255 * self.opacity))
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(QPointF(0, 0), self.ring_radius, self.ring_radius)

    def update_effect(self):
        self.ring_radius += 2
        self.opacity -= 0.05
        if self.ring_radius > self.max_radius or self.opacity <= 0:
            self.timer.stop()
            if self.scene_ref:
                self.scene_ref.removeItem(self)
        else:
            self.update()