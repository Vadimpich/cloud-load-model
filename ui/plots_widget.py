# -*- coding: utf-8 -*-
"""
Виджет с графиками в реальном времени.

Использует pyqtgraph для отображения временных рядов:
- Длина очереди
- Количество активных узлов
- Среднее время отклика
"""

import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PyQt6.QtCore import Qt
from typing import Dict, List


class PlotsWidget(QWidget):
    """
    Виджет с тремя графиками для отображения метрик в реальном времени.
    
    Графики:
    1. Длина очереди vs время
    2. Количество активных узлов vs время
    3. Среднее время отклика vs время
    """
    
    def __init__(self):
        """Инициализирует виджет с графиками."""
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Создает интерфейс с графиками."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Разделитель для трех графиков
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # График 1: Длина очереди
        self.queue_plot = pg.PlotWidget(title="Длина очереди")
        self.queue_plot.setLabel('left', 'Запросов в очереди')
        self.queue_plot.setLabel('bottom', 'Время моделирования')
        self.queue_plot.showGrid(x=True, y=True, alpha=0.3)
        self.queue_plot.setYRange(0, 50, padding=0)
        self.queue_curve = self.queue_plot.plot(pen=pg.mkPen(color='r', width=2))
        splitter.addWidget(self.queue_plot)
        
        # График 2: Количество узлов
        self.nodes_plot = pg.PlotWidget(title="Количество активных узлов")
        self.nodes_plot.setLabel('left', 'Количество узлов')
        self.nodes_plot.setLabel('bottom', 'Время моделирования')
        self.nodes_plot.showGrid(x=True, y=True, alpha=0.3)
        self.nodes_plot.setYRange(0, 15, padding=0)
        self.nodes_curve = self.nodes_plot.plot(pen=pg.mkPen(color='b', width=2))
        splitter.addWidget(self.nodes_plot)
        
        # График 3: Среднее время отклика
        self.response_plot = pg.PlotWidget(title="Среднее время отклика")
        self.response_plot.setLabel('left', 'Время отклика')
        self.response_plot.setLabel('bottom', 'Время моделирования')
        self.response_plot.showGrid(x=True, y=True, alpha=0.3)
        self.response_plot.setYRange(0, 10, padding=0)
        self.response_curve = self.response_plot.plot(pen=pg.mkPen(color='g', width=2))
        splitter.addWidget(self.response_plot)
        
        # Устанавливаем равные размеры для графиков
        splitter.setSizes([333, 333, 334])
        
        layout.addWidget(splitter)
        
        # Данные для графиков
        self.time_data: List[float] = []
        self.queue_data: List[int] = []
        self.nodes_data: List[int] = []
        self.response_data: List[float] = []
        
        # Максимальное количество точек для отображения (для производительности)
        self.max_points = 5000
    
    def update_data(self, time_series: Dict[str, List]):
        """
        Обновляет графики новыми данными.
        
        Args:
            time_series: Словарь с временными рядами:
                - 'time': список времени
                - 'queue_length': список длин очереди
                - 'nodes_count': список количества узлов
                - 'avg_response_time': список средних времен отклика
        """
        time = time_series.get('time', [])
        queue_length = time_series.get('queue_length', [])
        nodes_count = time_series.get('nodes_count', [])
        avg_response_time = time_series.get('avg_response_time', [])
        
        # Обновляем данные
        self.time_data = time
        self.queue_data = queue_length
        self.nodes_data = nodes_count
        self.response_data = avg_response_time
        
        # Ограничиваем количество точек для производительности
        if len(self.time_data) > self.max_points:
            # Берем последние max_points точек
            start_idx = len(self.time_data) - self.max_points
            self.time_data = self.time_data[start_idx:]
            self.queue_data = self.queue_data[start_idx:]
            self.nodes_data = self.nodes_data[start_idx:]
            self.response_data = self.response_data[start_idx:]
        
        # Обновляем графики
        if self.time_data:
            self.queue_curve.setData(self.time_data, self.queue_data)
            self.nodes_curve.setData(self.time_data, self.nodes_data)
            self.response_curve.setData(self.time_data, self.response_data)
            
            # Автоматическое масштабирование по X
            if len(self.time_data) > 1:
                x_min = min(self.time_data)
                x_max = max(self.time_data)
                x_range = x_max - x_min
                if x_range > 0:
                    self.queue_plot.setXRange(x_min - x_range * 0.05, x_max + x_range * 0.05, padding=0)
                    self.nodes_plot.setXRange(x_min - x_range * 0.05, x_max + x_range * 0.05, padding=0)
                    self.response_plot.setXRange(x_min - x_range * 0.05, x_max + x_range * 0.05, padding=0)
    
    def reset(self):
        """Сбрасывает все графики."""
        self.time_data.clear()
        self.queue_data.clear()
        self.nodes_data.clear()
        self.response_data.clear()
        
        self.queue_curve.setData([], [])
        self.nodes_curve.setData([], [])
        self.response_curve.setData([], [])

