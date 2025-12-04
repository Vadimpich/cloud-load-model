# -*- coding: utf-8 -*-
"""
Поток симуляции для интеграции SimPy и PyQt.

Запускает симуляцию в отдельном потоке и передает данные в GUI
через сигналы PyQt.
"""

import simpy
import time
from PyQt6.QtCore import QThread, pyqtSignal
from typing import Dict, Any

from model.core import CloudSystemModel
from model.load_balancer import LoadBalancer
from model.autoscaler import AutoScaler
from model.metrics import MetricsCollector


class SimulationThread(QThread):
    """
    Поток для выполнения симуляции SimPy.
    
    Запускает модель в отдельном потоке и периодически отправляет
    обновления состояния в GUI через сигналы.
    """
    
    # Сигналы для передачи данных в GUI
    state_updated = pyqtSignal(dict)  # Обновление состояния системы
    metrics_updated = pyqtSignal(dict)  # Обновление временных рядов
    stats_updated = pyqtSignal(dict)  # Обновление агрегированных метрик
    log_signal = pyqtSignal(str, str)  # Лог сообщение (message, level)
    finished_signal = pyqtSignal()  # Симуляция завершена
    error_signal = pyqtSignal(str)  # Ошибка при симуляции
    
    def __init__(self, settings: Dict[str, Any]):
        """
        Инициализирует поток симуляции.
        
        Args:
            settings: Словарь с параметрами модели
        """
        super().__init__()
        self.settings = settings
        self.is_paused = False
        self.should_stop = False
        
        # Компоненты модели (будут созданы в run)
        self.env = None
        self.model = None
        self.load_balancer = None
        self.autoscaler = None
        self.metrics_collector = None
    
    def run(self):
        """Запускает симуляцию в потоке."""
        try:
            # Создаем SimPy окружение
            self.env = simpy.Environment()
            
            self.log_signal.emit("Инициализация модели...", "INFO")
            
            # Создаем модель
            self.model = CloudSystemModel(
                env=self.env,
                lambda_rate=self.settings['lambda_rate'],
                service_time_min=self.settings['service_time_min'],
                service_time_max=self.settings['service_time_max'],
                net_delay_min=self.settings['net_delay_min'],
                net_delay_max=self.settings['net_delay_max'],
                max_requests_in_flight=self.settings.get('max_requests_in_flight'),
                initial_nodes=self.settings['initial_nodes'],
                node_capacity=1,
                max_wait_time=self.settings.get('max_wait_time'),
            )
            
            # Передаем функцию логирования в модель
            self.model.set_log_callback(lambda msg, level="INFO": self.log_signal.emit(msg, level))
            
            # Создаем балансировщик нагрузки
            self.load_balancer = LoadBalancer()
            
            # Создаем сборщик метрик
            self.metrics_collector = MetricsCollector()
            if 'sla_threshold' in self.settings and self.settings['sla_threshold']:
                self.metrics_collector.set_sla_threshold(self.settings['sla_threshold'])
                self.log_signal.emit(f"SLA порог установлен: {self.settings['sla_threshold']}", "INFO")
            
            # Создаем автомасштабировщик
            def get_metrics():
                return self.metrics_collector.get_current_metrics(self.model)
            
            self.autoscaler = AutoScaler(
                env=self.env,
                model=self.model,
                min_nodes=self.settings['min_nodes'],
                max_nodes=self.settings['max_nodes'],
                low_threshold=self.settings['low_threshold'],
                high_threshold=self.settings['high_threshold'],
                control_interval=self.settings['control_interval'],
                scale_cooldown=self.settings['scale_cooldown'],
                get_metrics_callback=get_metrics,
            )
            
            # Передаем функцию логирования в автомасштабировщик
            self.autoscaler.set_log_callback(lambda msg, level="INFO": self.log_signal.emit(msg, level))
            
            # Запускаем процессы
            self.model.is_running = True
            self.autoscaler.is_running = True
            
            self.log_signal.emit(
                f"Модель инициализирована: λ={self.settings['lambda_rate']}, "
                f"узлов={self.settings['initial_nodes']}, "
                f"длительность={self.settings.get('simulation_duration', 100.0)}",
                "INFO"
            )
            
            # Запускаем генератор запросов
            self.env.process(self.model.request_generator())
            self.log_signal.emit("Генератор запросов запущен", "INFO")
            
            # Запускаем обработчик запросов
            self.env.process(self.model.request_processor(self.load_balancer))
            self.log_signal.emit("Обработчик запросов запущен", "INFO")
            
            # Запускаем контроллер автомасштабирования
            self.env.process(self.autoscaler.control_loop())
            self.log_signal.emit("Контроллер автомасштабирования запущен", "INFO")
            self.log_signal.emit("Симуляция началась", "INFO")
            
            # Запускаем цикл симуляции с периодическим обновлением GUI
            update_interval = 0.5  # Обновляем GUI каждые 0.5 единиц времени
            next_update_time = update_interval
            
            simulation_duration = self.settings.get('simulation_duration', 100.0)
            
            while self.env.now < simulation_duration and not self.should_stop:
                # Продвигаем симуляцию до следующего обновления
                target_time = min(next_update_time, simulation_duration)
                
                if not self.is_paused:
                    self.env.run(until=target_time)
                else:
                    # Если на паузе, просто ждем
                    import time
                    time.sleep(0.1)
                    continue
                
                # Обновляем метрики
                self.metrics_collector.update_requests(
                    self.model.processed_requests,
                    self.model.rejected_requests
                )
                
                # Получаем текущие метрики
                current_metrics = self.metrics_collector.get_current_metrics(self.model)
                
                # Записываем снимок состояния
                self.metrics_collector.record_snapshot(
                    sim_time=current_metrics['sim_time'],
                    queue_length=current_metrics['queue_length'],
                    nodes_count=current_metrics['active_nodes'],
                    avg_response_time=current_metrics['avg_response_time'],
                )
                
                # Отправляем обновления в GUI
                state = self.model.get_system_state()
                self.state_updated.emit(state)
                
                time_series = self.metrics_collector.get_time_series()
                self.metrics_updated.emit(time_series)
                
                aggregated = self.metrics_collector.get_aggregated_metrics()
                self.stats_updated.emit(aggregated)
                
                # Обновляем время следующего обновления
                next_update_time += update_interval
            
            # Финальное обновление
            self.metrics_collector.update_requests(
                self.model.processed_requests,
                self.model.rejected_requests
            )
            
            state = self.model.get_system_state()
            self.state_updated.emit(state)
            
            time_series = self.metrics_collector.get_time_series()
            self.metrics_updated.emit(time_series)
            
            aggregated = self.metrics_collector.get_aggregated_metrics()
            self.stats_updated.emit(aggregated)
            
            # Останавливаем процессы
            self.model.is_running = False
            self.autoscaler.is_running = False
            
            self.log_signal.emit("Симуляция завершена", "INFO")
            processed = len(self.model.processed_requests)
            rejected = len(self.model.rejected_requests)
            total = processed + rejected
            if total > 0:
                rejection_rate = (rejected / total) * 100
                self.log_signal.emit(
                    f"Итоги: всего={total}, обработано={processed}, "
                    f"отклонено={rejected} ({rejection_rate:.1f}%)",
                    "INFO"
                )
            
            self.finished_signal.emit()
            
        except Exception as e:
            import traceback
            error_msg = str(e)
            error_traceback = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            print("=" * 80)
            print("ОШИБКА В ПОТОКЕ СИМУЛЯЦИИ:")
            print("=" * 80)
            print(error_traceback)
            print("=" * 80)
            # Отправляем полную информацию об ошибке
            self.error_signal.emit(f"{error_msg}\n\nПодробности в консоли.")
    
    def pause(self):
        """Приостанавливает симуляцию."""
        self.is_paused = True
        if self.model:
            self.model.is_paused = True
        if self.autoscaler:
            self.autoscaler.is_paused = True
    
    def resume(self):
        """Возобновляет симуляцию."""
        self.is_paused = False
        if self.model:
            self.model.is_paused = False
        if self.autoscaler:
            self.autoscaler.is_paused = False
    
    def stop(self):
        """Останавливает симуляцию."""
        self.should_stop = True
        if self.model:
            self.model.is_running = False
        if self.autoscaler:
            self.autoscaler.is_running = False

