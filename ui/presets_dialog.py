# -*- coding: utf-8 -*-
"""
Диалог выбора пресета настроек.

Позволяет пользователю выбрать один из предустановленных сценариев экспериментов.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QTextEdit,
    QPushButton, QLabel, QDialogButtonBox
)
from PyQt6.QtCore import Qt
from utils.presets import PRESETS, Preset


class PresetsDialog(QDialog):
    """
    Диалог для выбора пресета настроек.
    
    Показывает список доступных пресетов с описаниями и позволяет
    применить выбранный пресет к настройкам модели.
    """
    
    def __init__(self, parent=None):
        """Инициализирует диалог выбора пресетов."""
        super().__init__(parent)
        self.setWindowTitle("Эксперименты - Выбор пресета")
        self.setMinimumSize(700, 500)
        self.selected_preset: Preset = None
        self.setup_ui()
    
    def setup_ui(self):
        """Создает интерфейс диалога."""
        layout = QVBoxLayout(self)
        
        # Заголовок
        title = QLabel("Выберите пресет для эксперимента:")
        title.setStyleSheet("font-size: 14pt; font-weight: bold; padding: 5px;")
        layout.addWidget(title)
        
        # Основной layout: список слева, описание справа
        main_layout = QHBoxLayout()
        
        # Список пресетов слева
        list_label = QLabel("Доступные пресеты:")
        list_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(list_label, stretch=0)
        
        self.presets_list = QListWidget()
        self.presets_list.setMinimumWidth(300)
        for preset in PRESETS:
            self.presets_list.addItem(preset.name)
        self.presets_list.currentRowChanged.connect(self.on_preset_selected)
        main_layout.addWidget(self.presets_list, stretch=1)
        
        # Описание справа
        desc_layout = QVBoxLayout()
        desc_label = QLabel("Описание:")
        desc_label.setStyleSheet("font-weight: bold;")
        desc_layout.addWidget(desc_label)
        
        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setMinimumHeight(300)
        # Стиль для читаемости в любой теме
        self.description_text.setStyleSheet(
            "background-color: #f5f5f5; "
            "color: #000000; "
            "padding: 10px; "
            "border: 1px solid #cccccc;"
        )
        desc_layout.addWidget(self.description_text)
        
        main_layout.addLayout(desc_layout, stretch=1)
        layout.addLayout(main_layout)
        
        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Выбираем первый пресет по умолчанию
        if self.presets_list.count() > 0:
            self.presets_list.setCurrentRow(0)
            self.on_preset_selected(0)
    
    def on_preset_selected(self, row: int):
        """
        Обработчик выбора пресета в списке.
        
        Args:
            row: Индекс выбранного элемента
        """
        if 0 <= row < len(PRESETS):
            preset = PRESETS[row]
            self.selected_preset = preset
            self.description_text.setText(preset.description)
    
    def get_selected_preset(self) -> Preset:
        """
        Возвращает выбранный пресет.
        
        Returns:
            Выбранный Preset или None
        """
        return self.selected_preset

