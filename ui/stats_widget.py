# -*- coding: utf-8 -*-
"""
Виджет с итоговой статистикой моделирования.

Отображает агрегированные метрики в виде таблицы.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel
)
from PyQt6.QtCore import Qt
from typing import Dict, Any


class StatsWidget(QWidget):
    """
    Виджет для отображения агрегированных метрик моделирования.
    
    Показывает:
    - Общее количество запросов
    - Обработанные/отклоненные запросы
    - Среднее/максимальное время отклика
    - Средняя/максимальная длина очереди
    - Доля запросов в SLA
    """
    
    def __init__(self):
        """Инициализирует виджет статистики."""
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Создает интерфейс с таблицей статистики."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Заголовок
        title = QLabel("Итоговая статистика")
        title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(title)
        
        # Таблица статистики
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Метрика", "Значение"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Инициализируем строки таблицы
        self.metrics_labels = [
            "Всего запросов",
            "Обработано",
            "Отклонено (всего)",
            "  - из-за переполнения очереди",
            "  - по таймауту ожидания",
            "Доля отказов (%)",
            "Среднее время отклика",
            "Максимальное время отклика",
            "Минимальное время отклика",
            "Средняя длина очереди",
            "Максимальная длина очереди",
            "Соответствие SLA (%)",
        ]
        
        self.table.setRowCount(len(self.metrics_labels))
        for i, label in enumerate(self.metrics_labels):
            self.table.setItem(i, 0, QTableWidgetItem(label))
            self.table.setItem(i, 1, QTableWidgetItem("—"))
        
        layout.addWidget(self.table)
        layout.addStretch()
    
    def update_metrics(self, metrics: Dict[str, Any]):
        """
        Обновляет таблицу статистики новыми метриками.
        
        Args:
            metrics: Словарь с агрегированными метриками
        """
        # Форматируем значения для отображения
        def format_value(value, decimals=2):
            """Форматирует числовое значение."""
            if value is None:
                return "—"
            try:
                if isinstance(value, float):
                    import math
                    if math.isnan(value) or math.isinf(value):
                        return "—"
                    return f"{value:.{decimals}f}"
                float_val = float(value)
                import math
                if math.isnan(float_val) or math.isinf(float_val):
                    return "—"
                return f"{float_val:.{decimals}f}"
            except (ValueError, TypeError, OverflowError):
                return "—"
        
        # Обновляем значения в таблице
        values = [
            format_value(metrics.get('total_requests', 0), 0),
            format_value(metrics.get('processed_requests', 0), 0),
            format_value(metrics.get('rejected_requests', 0), 0),
            format_value(metrics.get('rejected_queue_full', 0), 0),
            format_value(metrics.get('rejected_wait_timeout', 0), 0),
            format_value(metrics.get('rejection_rate', 0.0), 2),
            format_value(metrics.get('avg_response_time', 0.0), 3),
            format_value(metrics.get('max_response_time', 0.0), 3),
            format_value(metrics.get('min_response_time', 0.0), 3),
            format_value(metrics.get('avg_queue_length', 0.0), 2),
            format_value(metrics.get('max_queue_length', 0), 0),
            format_value(metrics.get('sla_compliance_rate', 0.0), 2),
        ]
        
        for i, value in enumerate(values):
            item = self.table.item(i, 1)
            if item:
                item.setText(value)
    
    def reset(self):
        """Сбрасывает статистику."""
        for i in range(self.table.rowCount()):
            item = self.table.item(i, 1)
            if item:
                item.setText("—")

