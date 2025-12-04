# -*- coding: utf-8 -*-
"""
Виджет для отображения логов симуляции.

Показывает все действия, происходящие в модели: генерация запросов,
обработка, масштабирование, отказы и т.д.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt
from typing import Optional


class LogsWidget(QWidget):
    """
    Виджет для отображения логов симуляции.
    
    Показывает все события моделирования в хронологическом порядке.
    """
    
    def __init__(self):
        """Инициализирует виджет логов."""
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Создает интерфейс виджета логов."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Панель управления
        controls_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("Очистить")
        self.clear_btn.clicked.connect(self.clear_logs)
        controls_layout.addWidget(self.clear_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Текстовое поле для логов
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setFontFamily("Consolas")
        self.logs_text.setFontPointSize(9)
        self.logs_text.setStyleSheet(
            "background-color: #1e1e1e; "
            "color: #d4d4d4; "
            "border: 1px solid #3c3c3c;"
        )
        layout.addWidget(self.logs_text)
    
    def add_log(self, message: str, level: str = "INFO"):
        """
        Добавляет запись в лог.
        
        Args:
            message: Текст сообщения
            level: Уровень логирования (INFO, WARNING, ERROR)
        """
        from datetime import datetime
        # Форматируем сообщение с временной меткой
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] {message}"
        
        # Добавляем в текстовое поле
        self.logs_text.append(formatted_message)
        
        # Прокручиваем вниз
        scrollbar = self.logs_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_logs(self):
        """Очищает все логи."""
        self.logs_text.clear()
    
    def reset(self):
        """Сбрасывает виджет."""
        self.clear_logs()

