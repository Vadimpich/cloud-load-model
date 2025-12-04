# -*- coding: utf-8 -*-
"""
Сбор и агрегация метрик модели облачного приложения.

Собирает временные ряды и агрегированные метрики для анализа
работы системы и отображения в GUI.
"""

from typing import List, Dict, Any, Optional
from collections import deque
from .core import Request, CloudSystemModel


class MetricsCollector:
    """
    Сборщик метрик для модели облачного приложения.
    
    Собирает временные ряды (длина очереди, число узлов, время отклика)
    и вычисляет агрегированные метрики.
    """
    
    def __init__(self, max_history_size: int = 10000):
        """
        Инициализирует сборщик метрик.
        
        Args:
            max_history_size: Максимальный размер истории временных рядов
        """
        self.max_history_size = max_history_size
        
        # Временные ряды
        self.time_series: List[float] = deque(maxlen=max_history_size)
        self.queue_length_series: List[int] = deque(maxlen=max_history_size)
        self.nodes_count_series: List[int] = deque(maxlen=max_history_size)
        self.avg_response_time_series: List[float] = deque(maxlen=max_history_size)
        
        # Агрегированные метрики
        self.total_requests = 0
        self.processed_requests: List[Request] = []
        self.rejected_requests: List[Request] = []
        
        # SLA параметры
        self.sla_threshold: Optional[float] = None  # Порог времени отклика для SLA
    
    def set_sla_threshold(self, threshold: float):
        """
        Устанавливает порог времени отклика для SLA.
        
        Args:
            threshold: Максимальное время отклика для соответствия SLA
        """
        self.sla_threshold = threshold
    
    def record_snapshot(
        self,
        sim_time: float,
        queue_length: int,
        nodes_count: int,
        avg_response_time: float = 0.0
    ):
        """
        Записывает снимок состояния системы.
        
        Args:
            sim_time: Текущее моделируемое время
            queue_length: Длина очереди
            nodes_count: Количество активных узлов
            avg_response_time: Среднее время отклика за период
        """
        self.time_series.append(sim_time)
        self.queue_length_series.append(queue_length)
        self.nodes_count_series.append(nodes_count)
        self.avg_response_time_series.append(avg_response_time)
    
    def update_requests(self, processed: List[Request], rejected: List[Request]):
        """
        Обновляет информацию о запросах.
        
        Args:
            processed: Список обработанных запросов
            rejected: Список отклоненных запросов
        """
        self.processed_requests = processed.copy()
        self.rejected_requests = rejected.copy()
        self.total_requests = len(processed) + len(rejected)
    
    def get_time_series(self) -> Dict[str, List]:
        """
        Возвращает временные ряды метрик.
        
        Returns:
            Словарь с временными рядами
        """
        return {
            'time': list(self.time_series),
            'queue_length': list(self.queue_length_series),
            'nodes_count': list(self.nodes_count_series),
            'avg_response_time': list(self.avg_response_time_series),
        }
    
    def get_aggregated_metrics(self) -> Dict[str, Any]:
        """
        Вычисляет и возвращает агрегированные метрики.
        
        Returns:
            Словарь с агрегированными метриками
        """
        # Подсчитываем отказы по причинам
        rejected_queue_full = sum(1 for r in self.rejected_requests 
                                  if r.rejected_reason == 'queue_full')
        rejected_wait_timeout = sum(1 for r in self.rejected_requests 
                                    if r.rejected_reason == 'wait_timeout')
        rejected_other = len(self.rejected_requests) - rejected_queue_full - rejected_wait_timeout
        
        metrics = {
            'total_requests': self.total_requests,
            'processed_requests': len(self.processed_requests),
            'rejected_requests': len(self.rejected_requests),
            'rejected_queue_full': rejected_queue_full,
            'rejected_wait_timeout': rejected_wait_timeout,
            'rejected_other': rejected_other,
            'rejection_rate': 0.0,
            'avg_response_time': 0.0,
            'max_response_time': 0.0,
            'min_response_time': 0.0,
            'avg_queue_length': 0.0,
            'max_queue_length': 0,
            'sla_compliance_rate': 0.0,
        }
        
        # Вычисляем метрики по обработанным запросам
        if self.processed_requests:
            response_times = [
                r.get_response_time() 
                for r in self.processed_requests 
                if r.get_response_time() is not None
            ]
            
            if response_times:
                metrics['avg_response_time'] = sum(response_times) / len(response_times)
                metrics['max_response_time'] = max(response_times)
                metrics['min_response_time'] = min(response_times)
                
                # Вычисляем долю запросов, соответствующих SLA
                if self.sla_threshold is not None:
                    sla_compliant = sum(1 for rt in response_times if rt <= self.sla_threshold)
                    metrics['sla_compliance_rate'] = sla_compliant / len(response_times) * 100.0
        
        # Вычисляем метрики по очереди (средняя по времени, а не по снимкам)
        if len(self.time_series) > 1 and len(self.queue_length_series) > 1:
            # Вычисляем среднюю длину очереди по времени (интеграл)
            total_area = 0.0
            total_time = 0.0
            for i in range(len(self.time_series) - 1):
                dt = self.time_series[i + 1] - self.time_series[i]
                queue_len = self.queue_length_series[i]
                total_area += queue_len * dt
                total_time += dt
            
            if total_time > 0:
                metrics['avg_queue_length'] = total_area / total_time
            else:
                metrics['avg_queue_length'] = self.queue_length_series[-1] if self.queue_length_series else 0.0
            
            metrics['max_queue_length'] = max(self.queue_length_series)
        elif self.queue_length_series:
            # Fallback: если недостаточно данных, используем простое среднее
            metrics['avg_queue_length'] = sum(self.queue_length_series) / len(self.queue_length_series)
            metrics['max_queue_length'] = max(self.queue_length_series)
        
        # Вычисляем долю отказов
        if self.total_requests > 0:
            metrics['rejection_rate'] = len(self.rejected_requests) / self.total_requests * 100.0
        
        return metrics
    
    def get_current_metrics(self, model: CloudSystemModel) -> Dict[str, Any]:
        """
        Получает текущие метрики из модели.
        
        Args:
            model: Модель облачного приложения
            
        Returns:
            Словарь с текущими метриками
        """
        # Вычисляем среднее время отклика
        processed = model.processed_requests
        avg_response_time = 0.0
        if processed:
            response_times = [
                r.get_response_time() 
                for r in processed 
                if r.get_response_time() is not None
            ]
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
        
        return {
            'sim_time': model.env.now,
            'queue_length': model.get_queue_length(),
            'active_nodes': len(model.get_active_nodes()),
            'avg_response_time': avg_response_time,
        }
    
    def reset(self):
        """Сбрасывает все собранные метрики."""
        self.time_series.clear()
        self.queue_length_series.clear()
        self.nodes_count_series.clear()
        self.avg_response_time_series.clear()
        
        self.total_requests = 0
        self.processed_requests.clear()
        self.rejected_requests.clear()

