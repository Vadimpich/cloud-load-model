# -*- coding: utf-8 -*-
"""
Контроллер автомасштабирования для облачного приложения.

Реализует реактивный пороговый контроллер с гистерезисом для динамического
изменения количества узлов обработки в зависимости от нагрузки.
"""

import simpy
from typing import List, Optional, Callable
from .core import CloudSystemModel


class AutoScaler:
    """
    Контроллер автомасштабирования с пороговой логикой и гистерезисом.
    
    Периодически анализирует метрики системы (длина очереди, время отклика)
    и принимает решения о масштабировании количества узлов.
    """
    
    def __init__(
        self,
        env: simpy.Environment,
        model: CloudSystemModel,
        min_nodes: int = 1,
        max_nodes: int = 10,
        low_threshold: float = 2.0,
        high_threshold: float = 10.0,
        control_interval: float = 5.0,
        scale_cooldown: float = 10.0,
        get_metrics_callback: Optional[Callable] = None,
    ):
        """
        Инициализирует контроллер автомасштабирования.
        
        Args:
            env: SimPy окружение
            model: Модель облачного приложения
            min_nodes: Минимальное количество узлов
            max_nodes: Максимальное количество узлов
            low_threshold: Нижний порог для уменьшения масштаба (длина очереди)
            high_threshold: Верхний порог для увеличения масштаба (длина очереди)
            control_interval: Интервал между проверками метрик
            scale_cooldown: Минимальное время между операциями масштабирования
            get_metrics_callback: Функция для получения метрик (опционально)
        """
        self.env = env
        self.model = model
        self.min_nodes = min_nodes
        self.max_nodes = max_nodes
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold
        self.control_interval = control_interval
        self.scale_cooldown = scale_cooldown
        self.get_metrics_callback = get_metrics_callback
        
        # Состояние контроллера
        self.last_scale_time = 0.0
        self.consecutive_low_intervals = 0  # Счетчик последовательных интервалов с низкой нагрузкой
        self.required_consecutive_low = 2  # Требуемое количество интервалов для уменьшения масштаба
        
        # История метрик для анализа
        self.metrics_history: List[dict] = []
        
        # Метрики за текущий интервал контроля
        self.interval_start_time = 0.0
        self.interval_queue_lengths: List[tuple] = []  # (time, queue_length)
        self.interval_response_times: List[float] = []
        
        # Флаги управления
        self.is_running = False
        self.is_paused = False
        
        # Callback для логирования
        self.log_callback = None
    
    def get_current_metrics(self) -> dict:
        """
        Получает текущие метрики системы.
        
        Returns:
            Словарь с метриками (queue_length, avg_response_time и т.д.)
        """
        if self.get_metrics_callback:
            return self.get_metrics_callback()
        
        # Базовая реализация: используем длину очереди
        queue_length = self.model.get_queue_length()
        
        # Вычисляем среднее время отклика из обработанных запросов
        processed = self.model.processed_requests
        avg_response_time = 0.0
        if processed:
            response_times = [r.get_response_time() for r in processed if r.get_response_time() is not None]
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
        
        return {
            'queue_length': queue_length,
            'avg_response_time': avg_response_time,
            'active_nodes': len(self.model.get_active_nodes()),
        }
    
    def should_scale_up(self, metrics: dict) -> bool:
        """
        Определяет, нужно ли увеличить количество узлов.
        
        Args:
            metrics: Текущие метрики системы
            
        Returns:
            True если нужно увеличить масштаб
        """
        queue_length = metrics.get('queue_length', 0)
        avg_response_time = metrics.get('avg_response_time', 0)
        
        # Увеличиваем масштаб, если очередь или время отклика превышают верхний порог
        condition = (queue_length > self.high_threshold or 
                    avg_response_time > self.high_threshold)
        
        # Проверяем ограничения
        current_nodes = len(self.model.get_active_nodes())
        can_scale = current_nodes < self.max_nodes
        
        # Проверяем cooldown
        time_since_last_scale = self.env.now - self.last_scale_time
        cooldown_ok = time_since_last_scale >= self.scale_cooldown
        
        return condition and can_scale and cooldown_ok
    
    def should_scale_down(self, metrics: dict) -> bool:
        """
        Определяет, нужно ли уменьшить количество узлов.
        
        Args:
            metrics: Текущие метрики системы
            
        Returns:
            True если нужно уменьшить масштаб
        """
        queue_length = metrics.get('queue_length', 0)
        avg_response_time = metrics.get('avg_response_time', 0)
        
        # Уменьшаем масштаб, если показатели стабильно ниже нижнего порога
        condition = (queue_length < self.low_threshold and 
                    avg_response_time < self.low_threshold)
        
        # Проверяем ограничения
        current_nodes = len(self.model.get_active_nodes())
        can_scale = current_nodes > self.min_nodes
        
        # Проверяем cooldown
        time_since_last_scale = self.env.now - self.last_scale_time
        cooldown_ok = time_since_last_scale >= self.scale_cooldown
        
        # Требуем несколько последовательных интервалов с низкой нагрузкой (гистерезис)
        if condition and can_scale and cooldown_ok:
            self.consecutive_low_intervals += 1
            return self.consecutive_low_intervals >= self.required_consecutive_low
        else:
            # Сбрасываем счетчик, если условие не выполнено
            self.consecutive_low_intervals = 0
            return False
    
    def set_log_callback(self, callback):
        """
        Устанавливает callback для логирования.
        
        Args:
            callback: Функция для логирования (message, level)
        """
        self.log_callback = callback
    
    def _log(self, message: str, level: str = "INFO"):
        """
        Логирует сообщение через callback.
        
        Args:
            message: Текст сообщения
            level: Уровень логирования
        """
        if self.log_callback:
            self.log_callback(message, level)
    
    def scale_up(self) -> bool:
        """
        Увеличивает количество узлов на единицу.
        
        Returns:
            True если масштабирование выполнено успешно
        """
        current_nodes = len(self.model.get_active_nodes())
        if current_nodes < self.max_nodes:
            self.model.add_node()
            self.last_scale_time = self.env.now
            self.consecutive_low_intervals = 0  # Сбрасываем счетчик при масштабировании
            new_nodes = len(self.model.get_active_nodes())
            self._log(
                f"МАСШТАБИРОВАНИЕ ВВЕРХ: добавлен узел. Узлов: {current_nodes} → {new_nodes}",
                "INFO"
            )
            return True
        return False
    
    def scale_down(self) -> bool:
        """
        Уменьшает количество узлов на единицу.
        
        Returns:
            True если масштабирование выполнено успешно
        """
        current_nodes = len(self.model.get_active_nodes())
        if current_nodes > self.min_nodes:
            self.model.remove_node()
            self.last_scale_time = self.env.now
            self.consecutive_low_intervals = 0  # Сбрасываем счетчик после масштабирования
            new_nodes = len(self.model.get_active_nodes())
            self._log(
                f"МАСШТАБИРОВАНИЕ ВНИЗ: удален узел. Узлов: {current_nodes} → {new_nodes}",
                "INFO"
            )
            return True
        return False
    
    def metrics_collector_loop(self):
        """
        Периодически собирает метрики для расчета средних значений за интервал.
        """
        while self.is_running:
            if self.is_paused:
                yield self.env.timeout(0.1)
                continue
            
            # Собираем метрики каждые 0.1 единицы времени
            yield self.env.timeout(0.1)
            
            if not self.is_running:
                break
            
            # Записываем текущую длину очереди
            current_queue_length = self.model.get_queue_length()
            self.interval_queue_lengths.append((self.env.now, current_queue_length))
    
    def control_loop(self):
        """
        Основной цикл контроллера автомасштабирования.
        
        Периодически анализирует метрики и принимает решения о масштабировании.
        Считает средние значения метрик за интервал контроля.
        """
        self.interval_start_time = self.env.now
        
        # Запускаем сборщик метрик
        self.env.process(self.metrics_collector_loop())
        
        while self.is_running:
            if self.is_paused:
                yield self.env.timeout(0.1)
                continue
            
            # Ждем до следующего интервала контроля
            yield self.env.timeout(self.control_interval)
            
            if not self.is_running:
                break
            
            # Вычисляем средние метрики за интервал контроля
            interval_end_time = self.env.now
            metrics = self._calculate_interval_metrics(interval_end_time)
            
            self.metrics_history.append({
                'time': self.env.now,
                **metrics
            })
            
            # Логируем метрики за интервал
            queue_len = metrics.get('queue_length', 0)
            avg_rt = metrics.get('avg_response_time', 0)
            nodes = metrics.get('active_nodes', 0)
            self._log(
                f"Интервал контроля (t={self.env.now:.1f}): очередь={queue_len:.1f}, "
                f"время отклика={avg_rt:.2f}, узлов={nodes}",
                "INFO"
            )
            
            # Принимаем решение о масштабировании на основе средних значений
            if self.should_scale_up(metrics):
                self.scale_up()
            elif self.should_scale_down(metrics):
                self.scale_down()
            else:
                # Логируем, если решение не принято
                current_nodes = len(self.model.get_active_nodes())
                if queue_len > self.high_threshold and current_nodes < self.max_nodes:
                    time_since_scale = self.env.now - self.last_scale_time
                    if time_since_scale < self.scale_cooldown:
                        self._log(
                            f"Масштабирование заблокировано: cooldown "
                            f"({time_since_scale:.1f} < {self.scale_cooldown})",
                            "INFO"
                        )
            
            # Сбрасываем метрики для следующего интервала
            self.interval_start_time = self.env.now
            self.interval_queue_lengths.clear()
            self.interval_response_times.clear()
    
    def _calculate_interval_metrics(self, interval_end_time: float) -> dict:
        """
        Вычисляет средние метрики за интервал контроля.
        
        Args:
            interval_end_time: Время окончания интервала
            
        Returns:
            Словарь со средними метриками за интервал
        """
        # Добавляем финальное значение в историю интервала
        current_queue_length = self.model.get_queue_length()
        if not self.interval_queue_lengths or self.interval_queue_lengths[-1][0] < interval_end_time:
            self.interval_queue_lengths.append((interval_end_time, current_queue_length))
        
        # Получаем среднее время отклика за интервал из обработанных запросов
        # (запросы, обработанные в этом интервале)
        processed = self.model.processed_requests
        interval_response_times = [
            r.get_response_time() 
            for r in processed 
            if (r.get_response_time() is not None and 
                r.finish_time is not None and 
                r.finish_time >= self.interval_start_time and
                r.finish_time <= interval_end_time)
        ]
        if interval_response_times:
            self.interval_response_times.extend(interval_response_times)
        
        # Вычисляем среднюю длину очереди за интервал (по времени)
        avg_queue_length = 0.0
        if len(self.interval_queue_lengths) > 1:
            total_area = 0.0
            total_time = 0.0
            for i in range(len(self.interval_queue_lengths) - 1):
                t1, q1 = self.interval_queue_lengths[i]
                t2, q2 = self.interval_queue_lengths[i + 1]
                dt = t2 - t1
                if dt > 0:
                    # Используем среднее значение между двумя точками
                    avg_q = (q1 + q2) / 2.0
                    total_area += avg_q * dt
                    total_time += dt
            
            if total_time > 0:
                avg_queue_length = total_area / total_time
            else:
                avg_queue_length = current_queue_length
        elif self.interval_queue_lengths:
            avg_queue_length = self.interval_queue_lengths[-1][1]
        else:
            avg_queue_length = current_queue_length
        
        # Вычисляем среднее время отклика за интервал
        avg_response_time = 0.0
        if self.interval_response_times:
            avg_response_time = sum(self.interval_response_times) / len(self.interval_response_times)
        elif processed:
            # Fallback: используем общее среднее, если нет данных за интервал
            response_times = [r.get_response_time() for r in processed if r.get_response_time() is not None]
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
        
        return {
            'queue_length': avg_queue_length,  # Средняя длина очереди за интервал
            'avg_response_time': avg_response_time,  # Среднее время отклика за интервал
            'active_nodes': len(self.model.get_active_nodes()),
        }
    
    def reset(self):
        """Сбрасывает состояние контроллера."""
        self.last_scale_time = 0.0
        self.consecutive_low_intervals = 0
        self.metrics_history.clear()

