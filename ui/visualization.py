# -*- coding: utf-8 -*-
"""
Визуализация системы в реальном времени.

Компактная панель мониторинга с сеткой узлов, индикаторами и мини-графиками.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QProgressBar, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush
import pyqtgraph as pg
from typing import Dict, Any, List
from collections import deque
import os


class NodeTile(QWidget):
    """Плитка узла с индикацией состояния и загрузки."""
    
    def __init__(self, node_id: int, parent=None):
        super().__init__(parent)
        self.node_id = node_id
        self.is_busy = False
        self.load = 0.0  # Загрузка от 0.0 до 1.0
        self.setMinimumSize(80, 80)
        self.setMaximumSize(120, 120)
        self.setup_ui()
    
    def setup_ui(self):
        """Создает интерфейс плитки."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        # ID узла
        self.id_label = QLabel(f"Узел {self.node_id}")
        self.id_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.id_label.setStyleSheet("font-weight: bold; font-size: 10pt;")
        layout.addWidget(self.id_label)
        
        # Индикатор состояния
        self.status_label = QLabel("IDLE")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 9pt;")
        layout.addWidget(self.status_label)
        
        # Прогресс-бар загрузки
        self.load_bar = QProgressBar()
        self.load_bar.setRange(0, 100)
        self.load_bar.setValue(0)
        self.load_bar.setTextVisible(True)
        self.load_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #333;
                border-radius: 3px;
                text-align: center;
                height: 15px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.load_bar)
    
    def update_state(self, is_busy: bool, load: float):
        """
        Обновляет состояние узла.
        
        Args:
            is_busy: Узел занят обработкой
            load: Загрузка узла (0.0 - 1.0)
        """
        self.is_busy = is_busy
        self.load = load
        
        # Обновляем статус
        if is_busy:
            self.status_label.setText("BUSY")
            self.status_label.setStyleSheet("font-size: 9pt; color: #ff6b6b; font-weight: bold;")
            self.setStyleSheet("background-color: #fff3cd; border: 2px solid #ffc107; border-radius: 5px;")
        else:
            self.status_label.setText("IDLE")
            self.status_label.setStyleSheet("font-size: 9pt; color: #4CAF50;")
            self.setStyleSheet("background-color: #d4edda; border: 2px solid #28a745; border-radius: 5px;")
        
        # Обновляем прогресс-бар
        self.load_bar.setValue(int(load * 100))
        
        # Меняем цвет прогресс-бара в зависимости от загрузки
        if load > 0.8:
            color = "#f44336"  # Красный
        elif load > 0.5:
            color = "#ff9800"  # Оранжевый
        else:
            color = "#4CAF50"  # Зеленый
        
        self.load_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #333;
                border-radius: 3px;
                text-align: center;
                height: 15px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 2px;
            }}
        """)


class SystemVisualization(QWidget):
    """
    Компактная панель мониторинга системы в реальном времени.
    
    Отображает:
    - Сетку узлов с состоянием и загрузкой
    - Индикатор очереди
    - Мини-графики метрик
    """
    
    def __init__(self):
        """Инициализирует виджет визуализации."""
        super().__init__()
        self.setup_ui()
        self.current_state = {
            'queue_length': 0,
            'queue_capacity': 100,
            'active_nodes': 0,
            'total_nodes': 0,
            'avg_response_time': 0.0,
            'sla_compliance_rate': 0.0,
            'processed_requests': 0,
            'rejected_requests': 0,
        }
        
        # Данные для мини-графиков (последние 100 точек)
        self.max_history = 100
        self.queue_history = deque(maxlen=self.max_history)
        self.response_time_history = deque(maxlen=self.max_history)
        self.sla_history = deque(maxlen=self.max_history)
        self.nodes_history = deque(maxlen=self.max_history)
        self.time_history = deque(maxlen=self.max_history)
        self.time_counter = 0
        
        # Узлы
        self.node_tiles: List[NodeTile] = []
    
    def setup_ui(self):
        """Создает интерфейс визуализации."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Заголовок
        title = QLabel("Мониторинг системы в реальном времени")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 14pt; font-weight: bold; padding: 5px;")
        layout.addWidget(title)
        
        # Основной контейнер - две колонки
        main_layout = QHBoxLayout()
        
        # Левая колонка: узлы и очередь
        left_panel = QVBoxLayout()
        
        # Группа: Узлы
        nodes_group = QGroupBox("Узлы обработки")
        nodes_layout = QVBoxLayout()
        
        self.nodes_container = QWidget()
        self.nodes_grid = QGridLayout(self.nodes_container)
        self.nodes_grid.setSpacing(5)
        nodes_layout.addWidget(self.nodes_container)
        
        nodes_group.setLayout(nodes_layout)
        left_panel.addWidget(nodes_group)
        
        # Группа: Очередь
        queue_group = QGroupBox("Очередь запросов")
        queue_layout = QVBoxLayout()
        
        self.queue_label = QLabel("Очередь: 0 / 100")
        self.queue_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        queue_layout.addWidget(self.queue_label)
        
        self.queue_bar = QProgressBar()
        self.queue_bar.setRange(0, 100)
        self.queue_bar.setValue(0)
        self.queue_bar.setTextVisible(True)
        self.queue_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #333;
                border-radius: 5px;
                text-align: center;
                height: 30px;
                font-size: 11pt;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:0.7 #ff9800, stop:1 #f44336);
                border-radius: 3px;
            }
        """)
        queue_layout.addWidget(self.queue_bar)
        
        queue_group.setLayout(queue_layout)
        left_panel.addWidget(queue_group)
        
        # Статистика
        stats_group = QGroupBox("Статистика")
        stats_layout = QGridLayout()
        
        self.processed_label = QLabel("Обработано: 0")
        self.processed_label.setStyleSheet("font-size: 10pt;")
        stats_layout.addWidget(self.processed_label, 0, 0)
        
        self.rejected_label = QLabel("Отклонено: 0")
        self.rejected_label.setStyleSheet("font-size: 10pt;")
        stats_layout.addWidget(self.rejected_label, 0, 1)
        
        self.avg_response_label = QLabel("Ср. время отклика: 0.00")
        self.avg_response_label.setStyleSheet("font-size: 10pt;")
        stats_layout.addWidget(self.avg_response_label, 1, 0)
        
        self.sla_label = QLabel("SLA: 0.0%")
        self.sla_label.setStyleSheet("font-size: 10pt;")
        stats_layout.addWidget(self.sla_label, 1, 1)
        
        stats_group.setLayout(stats_layout)
        left_panel.addWidget(stats_group)
        
        main_layout.addLayout(left_panel, stretch=1)
        
        # Правая колонка: мини-графики
        right_panel = QVBoxLayout()
        
        # Мини-график: Длина очереди
        self.queue_plot = pg.PlotWidget(title="Длина очереди")
        self.queue_plot.setLabel('left', 'Запросов')
        self.queue_plot.setLabel('bottom', 'Время')
        self.queue_plot.showGrid(x=True, y=True, alpha=0.3)
        self.queue_plot.setFixedHeight(120)
        self.queue_plot.setYRange(0, 50, padding=0)
        self.queue_curve = self.queue_plot.plot(pen=pg.mkPen(color='r', width=2))
        right_panel.addWidget(self.queue_plot)
        
        # Мини-график: Время отклика
        self.response_plot = pg.PlotWidget(title="Среднее время отклика")
        self.response_plot.setLabel('left', 'Время')
        self.response_plot.setLabel('bottom', 'Время')
        self.response_plot.showGrid(x=True, y=True, alpha=0.3)
        self.response_plot.setFixedHeight(120)
        self.response_plot.setYRange(0, 10, padding=0)
        self.response_curve = self.response_plot.plot(pen=pg.mkPen(color='g', width=2))
        right_panel.addWidget(self.response_plot)
        
        # Мини-график: SLA%
        self.sla_plot = pg.PlotWidget(title="SLA соответствие")
        self.sla_plot.setLabel('left', '%')
        self.sla_plot.setLabel('bottom', 'Время')
        self.sla_plot.showGrid(x=True, y=True, alpha=0.3)
        self.sla_plot.setFixedHeight(120)
        self.sla_plot.setYRange(0, 100, padding=0)
        self.sla_curve = self.sla_plot.plot(pen=pg.mkPen(color='b', width=2))
        right_panel.addWidget(self.sla_plot)
        
        # Мини-график: Количество узлов
        self.nodes_plot = pg.PlotWidget(title="Активные узлы")
        self.nodes_plot.setLabel('left', 'Узлов')
        self.nodes_plot.setLabel('bottom', 'Время')
        self.nodes_plot.showGrid(x=True, y=True, alpha=0.3)
        self.nodes_plot.setFixedHeight(120)
        self.nodes_plot.setYRange(0, 15, padding=0)
        self.nodes_curve = self.nodes_plot.plot(pen=pg.mkPen(color='y', width=2))
        right_panel.addWidget(self.nodes_plot)
        
        main_layout.addLayout(right_panel, stretch=1)
        
        layout.addLayout(main_layout)
        
        # Кнопка сохранения
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        self.save_btn = QPushButton("Сохранить графики в PNG")
        self.save_btn.clicked.connect(self.save_graphs)
        save_layout.addWidget(self.save_btn)
        layout.addLayout(save_layout)
    
    def _update_nodes_grid(self, total_nodes: int):
        """
        Обновляет сетку узлов.
        
        Args:
            total_nodes: Общее количество узлов
        """
        # Очищаем старые плитки
        for tile in self.node_tiles:
            tile.deleteLater()
        self.node_tiles.clear()
        
        # Вычисляем оптимальное количество колонок (примерно 4-5)
        cols = min(5, max(2, int((total_nodes + 1) ** 0.5) + 1))
        
        # Создаем новые плитки
        for i in range(total_nodes):
            tile = NodeTile(i)
            row = i // cols
            col = i % cols
            self.nodes_grid.addWidget(tile, row, col)
            self.node_tiles.append(tile)
    
    def _get_node_load(self, node_id: int, state: dict) -> tuple:
        """
        Вычисляет загрузку узла.
        
        Args:
            node_id: ID узла
            state: Состояние системы
            
        Returns:
            (is_busy, load) где load от 0.0 до 1.0
        """
        # Упрощенная логика: если узел существует и активен, считаем загрузку
        # В реальности нужно получать данные из модели
        active_nodes = state.get('active_nodes', 0)
        if node_id < active_nodes:
            # Примерная загрузка на основе длины очереди
            queue_len = state.get('queue_length', 0)
            avg_load = min(1.0, queue_len / max(1, active_nodes * 2))
            return (True, avg_load)
        return (False, 0.0)
    
    def update_state(self, state: Dict[str, Any]):
        """
        Обновляет состояние визуализации.
        
        Args:
            state: Словарь с текущим состоянием системы
        """
        # Обновляем состояние
        total_nodes = state.get('total_nodes', state.get('active_nodes', 0))
        self.current_state.update({
            'queue_length': state.get('queue_length', 0),
            'queue_capacity': state.get('max_requests_in_flight', 100) or 100,
            'active_nodes': state.get('active_nodes', 0),
            'total_nodes': total_nodes,
            'avg_response_time': state.get('avg_response_time', 0.0),
            'sla_compliance_rate': state.get('sla_compliance_rate', 0.0),
            'processed_count': state.get('processed_count', 0),
            'rejected_count': state.get('rejected_count', 0),
        })
        
        # Обновляем очередь
        queue_len = self.current_state['queue_length']
        queue_capacity = self.current_state['queue_capacity']
        queue_percent = min(100, int((queue_len / max(1, queue_capacity)) * 100))
        
        self.queue_label.setText(f"Очередь: {queue_len} / {queue_capacity}")
        self.queue_bar.setMaximum(queue_capacity)
        self.queue_bar.setValue(queue_len)
        self.queue_bar.setFormat(f"{queue_len} / {queue_capacity}")
        
        # Обновляем сетку узлов
        total_nodes = self.current_state['total_nodes']
        if len(self.node_tiles) != total_nodes:
            self._update_nodes_grid(total_nodes)
        
        # Обновляем состояние каждого узла
        for i, tile in enumerate(self.node_tiles):
            is_busy, load = self._get_node_load(i, state)
            tile.update_state(is_busy, load)
        
        # Обновляем статистику
        self.processed_label.setText(f"Обработано: {state.get('processed_count', 0)}")
        self.rejected_label.setText(f"Отклонено: {state.get('rejected_count', 0)}")
        
        # Обновляем мини-графики
        self.time_counter += 1
        self.time_history.append(self.time_counter)
        self.queue_history.append(queue_len)
        
        # Получаем метрики из временных рядов, если доступны
        if 'avg_response_time' in state:
            self.current_state['avg_response_time'] = state['avg_response_time']
            self.response_time_history.append(state['avg_response_time'])
        else:
            self.response_time_history.append(0.0)
        
        if 'sla_compliance_rate' in state:
            self.current_state['sla_compliance_rate'] = state['sla_compliance_rate']
            self.sla_history.append(state['sla_compliance_rate'])
        else:
            self.sla_history.append(0.0)
        
        self.nodes_history.append(self.current_state['active_nodes'])
        
        # Обновляем графики
        if len(self.time_history) > 1:
            time_list = list(self.time_history)
            self.queue_curve.setData(time_list, list(self.queue_history))
            self.response_curve.setData(time_list, list(self.response_time_history))
            self.sla_curve.setData(time_list, list(self.sla_history))
            self.nodes_curve.setData(time_list, list(self.nodes_history))
            
            # Автомасштабирование по X
            x_min = max(0, self.time_counter - self.max_history)
            x_max = self.time_counter
            
            # Используем сохраненные PlotWidget
            if hasattr(self, 'queue_plot'):
                self.queue_plot.setXRange(x_min, x_max, padding=0)
            if hasattr(self, 'response_plot'):
                self.response_plot.setXRange(x_min, x_max, padding=0)
            if hasattr(self, 'sla_plot'):
                self.sla_plot.setXRange(x_min, x_max, padding=0)
            if hasattr(self, 'nodes_plot'):
                self.nodes_plot.setXRange(x_min, x_max, padding=0)
        
        # Обновляем метки
        avg_rt = self.current_state.get('avg_response_time', 0.0)
        self.avg_response_label.setText(f"Ср. время отклика: {avg_rt:.2f}")
        
        sla = self.current_state.get('sla_compliance_rate', 0.0)
        self.sla_label.setText(f"SLA: {sla:.1f}%")
    
    def save_graphs(self):
        """Сохраняет графики в PNG файлы."""
        from PyQt6.QtWidgets import QFileDialog
        from datetime import datetime
        
        # Выбираем директорию для сохранения
        directory = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения")
        if not directory:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Сохраняем каждый график
        plots = [
            (self.queue_curve, "queue_length", "Длина очереди"),
            (self.response_curve, "response_time", "Среднее время отклика"),
            (self.sla_curve, "sla_compliance", "SLA соответствие"),
            (self.nodes_curve, "active_nodes", "Активные узлы"),
        ]
        
        saved_files = []
        
        # Используем сохраненные PlotWidget
        plots_to_save = []
        if hasattr(self, 'queue_plot'):
            plots_to_save.append((self.queue_plot, "queue_length", "Длина очереди"))
        if hasattr(self, 'response_plot'):
            plots_to_save.append((self.response_plot, "response_time", "Среднее время отклика"))
        if hasattr(self, 'sla_plot'):
            plots_to_save.append((self.sla_plot, "sla_compliance", "SLA соответствие"))
        if hasattr(self, 'nodes_plot'):
            plots_to_save.append((self.nodes_plot, "active_nodes", "Активные узлы"))
        
        for plot_widget, name, title in plots_to_save:
            try:
                filename = os.path.join(directory, f"{name}_{timestamp}.png")
                exporter = pg.exporters.ImageExporter(plot_widget)
                exporter.export(filename)
                saved_files.append(filename)
            except Exception as e:
                print(f"Ошибка при сохранении {name}: {e}")
        
        if saved_files:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "Графики сохранены",
                f"Сохранено {len(saved_files)} графиков в:\n{directory}"
            )
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Ошибка",
                "Не удалось сохранить графики. Убедитесь, что есть данные для сохранения."
            )
