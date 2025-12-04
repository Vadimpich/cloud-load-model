# -*- coding: utf-8 -*-
"""
Панель настроек модели.

Содержит поля ввода и слайдеры для всех параметров моделирования.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QDoubleSpinBox, QSpinBox, QPushButton, QGroupBox,
    QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal


class SettingsPanel(QWidget):
    """
    Панель настроек параметров модели.
    
    Содержит все настраиваемые параметры:
    - Параметры нагрузки (lambda, service_time)
    - Параметры сети (задержки)
    - Параметры автомасштабирования
    - Управление симуляцией
    """
    
    # Сигналы
    start_signal = pyqtSignal()
    pause_signal = pyqtSignal()
    resume_signal = pyqtSignal()
    stop_signal = pyqtSignal()
    reset_signal = pyqtSignal()
    
    def __init__(self):
        """Инициализирует панель настроек."""
        super().__init__()
        self.setFixedWidth(350)
        self.setup_ui()
    
    def setup_ui(self):
        """Создает интерфейс панели настроек."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Группа: Параметры нагрузки
        load_group = QGroupBox("Параметры нагрузки")
        load_layout = QFormLayout()
        
        self.lambda_spin = QDoubleSpinBox()
        self.lambda_spin.setRange(0.1, 100.0)
        self.lambda_spin.setValue(2.0)
        self.lambda_spin.setSingleStep(0.1)
        self.lambda_spin.setDecimals(2)
        load_layout.addRow("λ (интенсивность):", self.lambda_spin)
        
        self.service_time_min_spin = QDoubleSpinBox()
        self.service_time_min_spin.setRange(0.1, 10.0)
        self.service_time_min_spin.setValue(0.5)
        self.service_time_min_spin.setSingleStep(0.1)
        self.service_time_min_spin.setDecimals(2)
        load_layout.addRow("Время обработки (мин):", self.service_time_min_spin)
        
        self.service_time_max_spin = QDoubleSpinBox()
        self.service_time_max_spin.setRange(0.1, 10.0)
        self.service_time_max_spin.setValue(2.0)
        self.service_time_max_spin.setSingleStep(0.1)
        self.service_time_max_spin.setDecimals(2)
        load_layout.addRow("Время обработки (макс):", self.service_time_max_spin)
        
        load_group.setLayout(load_layout)
        layout.addWidget(load_group)
        
        # Группа: Параметры сети
        network_group = QGroupBox("Параметры сети")
        network_layout = QFormLayout()
        
        self.net_delay_min_spin = QDoubleSpinBox()
        self.net_delay_min_spin.setRange(0.0, 1.0)
        self.net_delay_min_spin.setValue(0.0)
        self.net_delay_min_spin.setSingleStep(0.01)
        self.net_delay_min_spin.setDecimals(3)
        network_layout.addRow("Задержка сети (мин):", self.net_delay_min_spin)
        
        self.net_delay_max_spin = QDoubleSpinBox()
        self.net_delay_max_spin.setRange(0.0, 1.0)
        self.net_delay_max_spin.setValue(0.1)
        self.net_delay_max_spin.setSingleStep(0.01)
        self.net_delay_max_spin.setDecimals(3)
        network_layout.addRow("Задержка сети (макс):", self.net_delay_max_spin)
        
        self.max_requests_spin = QSpinBox()
        self.max_requests_spin.setRange(0, 1000)
        self.max_requests_spin.setValue(100)
        self.max_requests_spin.setSpecialValueText("Без ограничений")
        network_layout.addRow("Макс. запросов:", self.max_requests_spin)
        
        network_group.setLayout(network_layout)
        layout.addWidget(network_group)
        
        # Группа: Автомасштабирование
        autoscale_group = QGroupBox("Автомасштабирование")
        autoscale_layout = QFormLayout()
        
        self.min_nodes_spin = QSpinBox()
        self.min_nodes_spin.setRange(1, 50)
        self.min_nodes_spin.setValue(1)
        autoscale_layout.addRow("Мин. узлов:", self.min_nodes_spin)
        
        self.max_nodes_spin = QSpinBox()
        self.max_nodes_spin.setRange(1, 50)
        self.max_nodes_spin.setValue(10)
        autoscale_layout.addRow("Макс. узлов:", self.max_nodes_spin)
        
        self.initial_nodes_spin = QSpinBox()
        self.initial_nodes_spin.setRange(1, 50)
        self.initial_nodes_spin.setValue(2)
        autoscale_layout.addRow("Начальных узлов:", self.initial_nodes_spin)
        
        self.low_threshold_spin = QDoubleSpinBox()
        self.low_threshold_spin.setRange(0.0, 100.0)
        self.low_threshold_spin.setValue(2.0)
        self.low_threshold_spin.setSingleStep(0.5)
        self.low_threshold_spin.setDecimals(1)
        autoscale_layout.addRow("Нижний порог:", self.low_threshold_spin)
        
        self.high_threshold_spin = QDoubleSpinBox()
        self.high_threshold_spin.setRange(0.0, 100.0)
        self.high_threshold_spin.setValue(10.0)
        self.high_threshold_spin.setSingleStep(0.5)
        self.high_threshold_spin.setDecimals(1)
        autoscale_layout.addRow("Верхний порог:", self.high_threshold_spin)
        
        self.control_interval_spin = QDoubleSpinBox()
        self.control_interval_spin.setRange(0.5, 60.0)
        self.control_interval_spin.setValue(5.0)
        self.control_interval_spin.setSingleStep(0.5)
        self.control_interval_spin.setDecimals(1)
        autoscale_layout.addRow("Интервал контроля:", self.control_interval_spin)
        
        self.scale_cooldown_spin = QDoubleSpinBox()
        self.scale_cooldown_spin.setRange(0.5, 60.0)
        self.scale_cooldown_spin.setValue(10.0)
        self.scale_cooldown_spin.setSingleStep(0.5)
        self.scale_cooldown_spin.setDecimals(1)
        autoscale_layout.addRow("Cooldown:", self.scale_cooldown_spin)
        
        autoscale_group.setLayout(autoscale_layout)
        layout.addWidget(autoscale_group)
        
        # Группа: Симуляция
        sim_group = QGroupBox("Симуляция")
        sim_layout = QFormLayout()
        
        self.sim_duration_spin = QDoubleSpinBox()
        self.sim_duration_spin.setRange(1.0, 10000.0)
        self.sim_duration_spin.setValue(100.0)
        self.sim_duration_spin.setSingleStep(10.0)
        self.sim_duration_spin.setDecimals(1)
        sim_layout.addRow("Длительность:", self.sim_duration_spin)
        
        sim_group.setLayout(sim_layout)
        layout.addWidget(sim_group)
        
        # Группа: SLA и отказы
        sla_group = QGroupBox("SLA и отказы")
        sla_layout = QFormLayout()
        
        self.sla_threshold_spin = QDoubleSpinBox()
        self.sla_threshold_spin.setRange(0.1, 100.0)
        self.sla_threshold_spin.setValue(5.0)
        self.sla_threshold_spin.setSingleStep(0.5)
        self.sla_threshold_spin.setDecimals(2)
        self.sla_threshold_spin.setSpecialValueText("Не задан")
        sla_layout.addRow("SLA порог (макс. время отклика):", self.sla_threshold_spin)
        
        self.max_wait_time_spin = QDoubleSpinBox()
        self.max_wait_time_spin.setRange(0.0, 100.0)
        self.max_wait_time_spin.setValue(10.0)
        self.max_wait_time_spin.setSingleStep(0.5)
        self.max_wait_time_spin.setDecimals(2)
        self.max_wait_time_spin.setSpecialValueText("Без ограничений")
        sla_layout.addRow("Макс. время ожидания в очереди:", self.max_wait_time_spin)
        
        sla_group.setLayout(sla_layout)
        layout.addWidget(sla_group)
        
        # Кнопки управления
        buttons_layout = QVBoxLayout()
        
        self.start_btn = QPushButton("Старт")
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.start_btn.clicked.connect(self.start_signal.emit)
        buttons_layout.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("Пауза")
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.pause_signal.emit)
        buttons_layout.addWidget(self.pause_btn)
        
        self.resume_btn = QPushButton("Продолжить")
        self.resume_btn.setEnabled(False)
        self.resume_btn.clicked.connect(self.resume_signal.emit)
        buttons_layout.addWidget(self.resume_btn)
        
        self.stop_btn = QPushButton("Стоп")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.stop_btn.clicked.connect(self.stop_signal.emit)
        buttons_layout.addWidget(self.stop_btn)
        
        self.reset_btn = QPushButton("Сброс")
        self.reset_btn.clicked.connect(self.reset_signal.emit)
        buttons_layout.addWidget(self.reset_btn)
        
        layout.addLayout(buttons_layout)
        layout.addStretch()
    
    def get_settings(self) -> dict:
        """
        Получает текущие настройки из всех полей.
        
        Returns:
            Словарь с параметрами модели
        """
        return {
            'lambda_rate': self.lambda_spin.value(),
            'service_time_min': self.service_time_min_spin.value(),
            'service_time_max': self.service_time_max_spin.value(),
            'net_delay_min': self.net_delay_min_spin.value(),
            'net_delay_max': self.net_delay_max_spin.value(),
            'max_requests_in_flight': self.max_requests_spin.value() if self.max_requests_spin.value() > 0 else None,
            'min_nodes': self.min_nodes_spin.value(),
            'max_nodes': self.max_nodes_spin.value(),
            'initial_nodes': self.initial_nodes_spin.value(),
            'low_threshold': self.low_threshold_spin.value(),
            'high_threshold': self.high_threshold_spin.value(),
            'control_interval': self.control_interval_spin.value(),
            'scale_cooldown': self.scale_cooldown_spin.value(),
            'simulation_duration': self.sim_duration_spin.value(),
            'sla_threshold': self.sla_threshold_spin.value() if self.sla_threshold_spin.value() > 0 else None,
            'max_wait_time': self.max_wait_time_spin.value() if self.max_wait_time_spin.value() > 0 else None,
        }
    
    def apply_preset(self, params: dict):
        """
        Применяет параметры пресета к полям настроек.
        
        Args:
            params: Словарь с параметрами пресета
        """
        # Параметры нагрузки
        if 'lambda_rate' in params:
            self.lambda_spin.setValue(params['lambda_rate'])
        if 'service_time_min' in params:
            self.service_time_min_spin.setValue(params['service_time_min'])
        if 'service_time_max' in params:
            self.service_time_max_spin.setValue(params['service_time_max'])
        
        # Параметры сети
        if 'net_delay_min' in params:
            self.net_delay_min_spin.setValue(params['net_delay_min'])
        if 'net_delay_max' in params:
            self.net_delay_max_spin.setValue(params['net_delay_max'])
        if 'max_requests_in_flight' in params:
            value = params['max_requests_in_flight']
            self.max_requests_spin.setValue(value if value is not None else 0)
        
        # Автомасштабирование
        if 'min_nodes' in params:
            self.min_nodes_spin.setValue(params['min_nodes'])
        if 'max_nodes' in params:
            self.max_nodes_spin.setValue(params['max_nodes'])
        if 'initial_nodes' in params:
            self.initial_nodes_spin.setValue(params['initial_nodes'])
        if 'low_threshold' in params:
            self.low_threshold_spin.setValue(params['low_threshold'])
        if 'high_threshold' in params:
            self.high_threshold_spin.setValue(params['high_threshold'])
        if 'control_interval' in params:
            self.control_interval_spin.setValue(params['control_interval'])
        if 'scale_cooldown' in params:
            self.scale_cooldown_spin.setValue(params['scale_cooldown'])
        
        # Симуляция
        if 'simulation_duration' in params:
            self.sim_duration_spin.setValue(params['simulation_duration'])
        
        # SLA и отказы
        if 'sla_threshold' in params:
            value = params['sla_threshold']
            self.sla_threshold_spin.setValue(value if value is not None else 0)
        if 'max_wait_time' in params:
            value = params['max_wait_time']
            self.max_wait_time_spin.setValue(value if value is not None else 0)
    
    def set_controls_enabled(self, running: bool, paused: bool):
        """
        Управляет состоянием кнопок управления.
        
        Args:
            running: Симуляция запущена
            paused: Симуляция на паузе
        """
        self.start_btn.setEnabled(not running)
        self.pause_btn.setEnabled(running and not paused)
        self.resume_btn.setEnabled(running and paused)
        self.stop_btn.setEnabled(running)
        self.reset_btn.setEnabled(not running)

