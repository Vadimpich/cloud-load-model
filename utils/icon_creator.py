# -*- coding: utf-8 -*-
"""
Утилита для создания иконки приложения.

Создает простую иконку облачка для приложения.
"""

from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPen
from PyQt6.QtCore import Qt, QSize


def create_cloud_icon(size=64):
    """
    Создает иконку облачка.
    
    Args:
        size: Размер иконки в пикселях
        
    Returns:
        QIcon с иконкой облачка
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Цвета
    cloud_color = QColor(100, 150, 255)  # Голубой
    shadow_color = QColor(70, 100, 200)  # Темно-голубой для тени
    
    # Рисуем облачко из нескольких кругов
    center_x = size // 2
    center_y = size // 2
    
    # Основные части облака
    circles = [
        (center_x - 15, center_y - 5, 18),   # Левая часть
        (center_x, center_y - 10, 20),        # Центральная верхняя
        (center_x + 15, center_y - 5, 18),    # Правая часть
        (center_x - 8, center_y + 5, 15),    # Левая нижняя
        (center_x + 8, center_y + 5, 15),    # Правая нижняя
    ]
    
    # Рисуем тень (немного смещена вправо и вниз)
    painter.setBrush(QBrush(shadow_color))
    painter.setPen(Qt.PenStyle.NoPen)
    for x, y, r in circles:
        painter.drawEllipse(x + 2, y + 2, r, r)
    
    # Рисуем основное облако
    painter.setBrush(QBrush(cloud_color))
    painter.setPen(QPen(QColor(80, 120, 200), 2))
    for x, y, r in circles:
        painter.drawEllipse(x, y, r, r)
    
    # Добавляем небольшие детали для объема
    highlight_color = QColor(150, 200, 255)
    painter.setBrush(QBrush(highlight_color))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(center_x - 12, center_y - 8, 8, 8)
    
    painter.end()
    
    icon = QIcon()
    icon.addPixmap(pixmap)
    
    return icon

