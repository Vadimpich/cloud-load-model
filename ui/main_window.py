# -*- coding: utf-8 -*-
"""
Главное окно приложения.

Содержит основную структуру интерфейса с вкладками для графиков,
статистики и визуализации, а также панель управления.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QStatusBar, QMenuBar, QMenu, QMessageBox, QDialog
)
from PyQt6.QtCore import Qt
from utils.icon_creator import create_cloud_icon
from .settings_panel import SettingsPanel
from .plots_widget import PlotsWidget
from .stats_widget import StatsWidget
from .visualization import SystemVisualization
from .logs_widget import LogsWidget
from .simulation_thread import SimulationThread
from .presets_dialog import PresetsDialog


class MainWindow(QMainWindow):
    """
    Главное окно приложения для моделирования облачного приложения.
    
    Содержит:
    - Панель настроек (слева)
    - Вкладки с графиками, статистикой и визуализацией (справа)
    - Меню и статусную строку
    """
    
    def __init__(self):
        """Инициализирует главное окно."""
        super().__init__()
        self.setWindowTitle("Модель нагрузки облачного приложения")
        self.setGeometry(100, 100, 1400, 900)
        
        # Устанавливаем иконку приложения
        icon = create_cloud_icon(64)
        self.setWindowIcon(icon)
        
        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Панель настроек (слева)
        self.settings_panel = SettingsPanel()
        main_layout.addWidget(self.settings_panel, stretch=0)
        
        # Правая часть - вкладки
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs, stretch=1)
        
        # Создаем виджеты для вкладок
        self.plots_widget = PlotsWidget()
        self.stats_widget = StatsWidget()
        self.visualization_widget = SystemVisualization()
        self.logs_widget = LogsWidget()
        
        # Добавляем вкладки
        self.tabs.addTab(self.plots_widget, "Графики")
        self.tabs.addTab(self.stats_widget, "Статистика")
        # self.tabs.addTab(self.visualization_widget, "Визуализация")  # Временно скрыто
        self.tabs.addTab(self.logs_widget, "Логи")
        
        # Создаем меню
        self._create_menu_bar()
        
        # Создаем статусную строку
        self.statusBar().showMessage("Готово к запуску")
        
        # Поток симуляции
        self.simulation_thread = None
        
        # Соединяем сигналы от панели настроек
        self._connect_signals()
    
    def _create_menu_bar(self):
        """Создает меню приложения."""
        menubar = self.menuBar()
        
        # Меню "Файл"
        file_menu = menubar.addMenu("Файл")
        exit_action = file_menu.addAction("Выход")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        
        # Меню "Эксперименты"
        experiments_menu = menubar.addMenu("Эксперименты")
        load_preset_action = experiments_menu.addAction("Загрузить пресет...")
        load_preset_action.setShortcut("Ctrl+P")
        load_preset_action.triggered.connect(self._load_preset)
        
        # Меню "Справка"
        help_menu = menubar.addMenu("Справка")
        about_action = help_menu.addAction("О программе")
        about_action.triggered.connect(self._show_about)
    
    def _load_preset(self):
        """Открывает диалог выбора пресета и применяет выбранный пресет."""
        dialog = PresetsDialog(self)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            preset = dialog.get_selected_preset()
            if preset:
                self._apply_preset(preset)
                self.update_status(f"Загружен пресет: {preset.name}")
    
    def _apply_preset(self, preset):
        """
        Применяет параметры пресета к панели настроек.
        
        Args:
            preset: Preset объект с параметрами
        """
        params = preset.get_parameters()
        self.settings_panel.apply_preset(params)
    
    def _show_about(self):
        """Показывает диалог 'О программе'."""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.about(
            self,
            "О программе",
            "Модель облачного приложения с Autoscaling\n\n"
            "Курсовая работа по дисциплине\n"
            "'Имитационное моделирование дискретных процессов'\n\n"
            "Использует SimPy для моделирования и PyQt6 для интерфейса.\n\n"
            "РТ5-71Б, Пичурин В.Е., Топорин Б.Г., 2025"
        )
    
    def _connect_signals(self):
        """Соединяет сигналы между компонентами."""
        # Подключаем сигналы от панели настроек
        self.settings_panel.start_signal.connect(self.start_simulation)
        self.settings_panel.pause_signal.connect(self.pause_simulation)
        self.settings_panel.resume_signal.connect(self.resume_simulation)
        self.settings_panel.stop_signal.connect(self.stop_simulation)
        self.settings_panel.reset_signal.connect(self.reset_simulation)
    
    def start_simulation(self):
        """Запускает симуляцию."""
        if self.simulation_thread and self.simulation_thread.isRunning():
            return
        
        # Получаем настройки
        settings = self.get_settings()
        
        # Очищаем логи
        self.logs_widget.clear_logs()
        self.add_log("=" * 60, "INFO")
        self.add_log("НАЧАЛО НОВОЙ СИМУЛЯЦИИ", "INFO")
        self.add_log("=" * 60, "INFO")
        
        # Создаем новый поток симуляции
        self.simulation_thread = SimulationThread(settings)
        
        # Подключаем сигналы
        self.simulation_thread.state_updated.connect(self.update_visualization)
        self.simulation_thread.metrics_updated.connect(self.update_plots)
        self.simulation_thread.stats_updated.connect(self.update_stats)
        self.simulation_thread.log_signal.connect(self.add_log)
        self.simulation_thread.finished_signal.connect(self.on_simulation_finished)
        self.simulation_thread.error_signal.connect(self.on_simulation_error)
        
        # Обновляем состояние кнопок
        self.settings_panel.set_controls_enabled(running=True, paused=False)
        
        # Запускаем поток
        self.simulation_thread.start()
        self.update_status("Симуляция запущена...")
    
    def pause_simulation(self):
        """Приостанавливает симуляцию."""
        if self.simulation_thread and self.simulation_thread.isRunning():
            self.simulation_thread.pause()
            self.add_log("Симуляция приостановлена", "INFO")
            self.settings_panel.set_controls_enabled(running=True, paused=True)
            self.update_status("Симуляция на паузе")
    
    def resume_simulation(self):
        """Возобновляет симуляцию."""
        if self.simulation_thread and self.simulation_thread.isRunning():
            self.simulation_thread.resume()
            self.add_log("Симуляция возобновлена", "INFO")
            self.settings_panel.set_controls_enabled(running=True, paused=False)
            self.update_status("Симуляция продолжается...")
    
    def stop_simulation(self):
        """Останавливает симуляцию."""
        if self.simulation_thread and self.simulation_thread.isRunning():
            self.add_log("Остановка симуляции...", "INFO")
            self.simulation_thread.stop()
            self.simulation_thread.wait(3000)  # Ждем до 3 секунд
            self.settings_panel.set_controls_enabled(running=False, paused=False)
            self.update_status("Симуляция остановлена")
    
    def reset_simulation(self):
        """Сбрасывает симуляцию."""
        self.stop_simulation()
        self.plots_widget.reset()
        self.stats_widget.reset()
        self.logs_widget.reset()
        self.update_status("Готово к запуску")
    
    def add_log(self, message: str, level: str = "INFO"):
        """
        Добавляет запись в лог.
        
        Args:
            message: Текст сообщения
            level: Уровень логирования
        """
        self.logs_widget.add_log(message, level)
    
    def on_simulation_finished(self):
        """Обработчик завершения симуляции."""
        self.settings_panel.set_controls_enabled(running=False, paused=False)
        self.update_status("Симуляция завершена")
    
    def on_simulation_error(self, error_message: str):
        """Обработчик ошибки симуляции."""
        print(f"Ошибка симуляции получена в GUI: {error_message}")
        QMessageBox.critical(
            self, 
            "Ошибка симуляции", 
            f"Произошла ошибка:\n{error_message}\n\n"
            f"Подробная информация выведена в консоль."
        )
        self.settings_panel.set_controls_enabled(running=False, paused=False)
        self.update_status("Ошибка при выполнении симуляции")
    
    def get_settings(self) -> dict:
        """
        Получает текущие настройки из панели настроек.
        
        Returns:
            Словарь с параметрами модели
        """
        return self.settings_panel.get_settings()
    
    def update_status(self, message: str):
        """
        Обновляет сообщение в статусной строке.
        
        Args:
            message: Текст сообщения
        """
        self.statusBar().showMessage(message)
    
    def update_plots(self, time_series: dict):
        """
        Обновляет графики новыми данными.
        
        Args:
            time_series: Словарь с временными рядами
        """
        self.plots_widget.update_data(time_series)
    
    def update_stats(self, metrics: dict):
        """
        Обновляет статистику новыми метриками.
        
        Args:
            metrics: Словарь с агрегированными метриками
        """
        self._last_stats = metrics  # Сохраняем для визуализации
        self.stats_widget.update_metrics(metrics)
    
    def update_visualization(self, state: dict):
        """
        Обновляет визуализацию системы.
        
        Args:
            state: Словарь с текущим состоянием системы
        """
        # Визуализация временно отключена
        # # Обогащаем состояние метриками из последних stats для визуализации
        # # Это нужно для отображения SLA% и других метрик
        # if hasattr(self, '_last_stats'):
        #     state.update({
        #         'sla_compliance_rate': self._last_stats.get('sla_compliance_rate', 0.0),
        #         'avg_response_time': self._last_stats.get('avg_response_time', 0.0),
        #         'processed_count': self._last_stats.get('processed_count', 0),
        #         'rejected_count': self._last_stats.get('rejected_count', 0),
        #     })
        # self.visualization_widget.update_state(state)
        pass

