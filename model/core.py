# -*- coding: utf-8 -*-
"""
Основные классы модели облачного приложения.

Содержит классы Request, StorageNode и CloudSystemModel для имитационного
моделирования облачного хранилища с динамическим масштабированием.
"""

import simpy
import numpy as np
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class Request:
    """
    Представляет входящий запрос пользователя.
    
    Attributes:
        request_id: Уникальный идентификатор запроса
        arrival_time: Время поступления запроса в систему
        start_time: Время начала обработки (None если еще не начата)
        finish_time: Время завершения обработки (None если еще не завершена)
        node_id: ID узла, обработавшего запрос (None если еще не назначен)
        rejected: Флаг отказа в обслуживании
        service_time: Время обработки запроса (генерируется при создании)
    """
    request_id: int
    arrival_time: float
    queue_entry_time: Optional[float] = None
    start_time: Optional[float] = None
    finish_time: Optional[float] = None
    node_id: Optional[int] = None
    rejected: bool = False
    rejected_reason: Optional[str] = None
    service_time: Optional[float] = None
    
    def get_response_time(self) -> Optional[float]:
        """
        Вычисляет время отклика запроса (от поступления до завершения).
        
        Returns:
            Время отклика в единицах моделируемого времени или None,
            если запрос еще не завершен.
        """
        if self.finish_time is not None and self.arrival_time is not None:
            return self.finish_time - self.arrival_time
        return None
    
    def get_wait_time(self) -> Optional[float]:
        """
        Вычисляет время ожидания в очереди.
        
        Returns:
            Время ожидания в очереди или None, если запрос еще не начал обрабатываться.
        """
        if self.start_time is not None and self.queue_entry_time is not None:
            return self.start_time - self.queue_entry_time
        return None


class StorageNode:
    """
    Узел обработки запросов (серверный узел).
    
    Каждый узел имеет ограниченную пропускную способность (capacity)
    и может обрабатывать несколько запросов одновременно.
    """
    
    def __init__(self, env: simpy.Environment, node_id: int, capacity: int = 1):
        """
        Инициализирует узел обработки.
        
        Args:
            env: SimPy окружение
            node_id: Уникальный идентификатор узла
            capacity: Количество одновременных запросов, которые может обработать узел
        """
        self.env = env
        self.node_id = node_id
        self.capacity = capacity
        # SimPy Resource для ограничения параллельной обработки
        self.resource = simpy.Resource(env, capacity=capacity)
        self.is_active = True
        
    def process_request(self, request: Request, service_time: float) -> simpy.Process:
        """
        Обрабатывает запрос на узле.
        
        Args:
            request: Запрос для обработки
            service_time: Время обработки запроса
            
        Yields:
            SimPy событие завершения обработки
        """
        request.node_id = self.node_id
        request.start_time = self.env.now
        
        # Захватываем ресурс узла
        with self.resource.request() as req:
            yield req
            # Обработка запроса
            yield self.env.timeout(service_time)
            request.finish_time = self.env.now


class CloudSystemModel:
    """
    Основная модель облачного приложения.
    
    Управляет генерацией запросов, очередью, пулом узлов обработки
    и сбором метрик.
    """
    
    def __init__(
        self,
        env: simpy.Environment,
        lambda_rate: float = 1.0,
        service_time_min: float = 0.5,
        service_time_max: float = 2.0,
        net_delay_min: float = 0.0,
        net_delay_max: float = 0.1,
        max_requests_in_flight: Optional[int] = None,
        initial_nodes: int = 2,
        node_capacity: int = 1,
        max_wait_time: Optional[float] = None,
    ):
        """
        Инициализирует модель облачного приложения.
        
        Args:
            env: SimPy окружение
            lambda_rate: Интенсивность входящего потока запросов (запросов в единицу времени)
            service_time_min: Минимальное время обработки запроса
            service_time_max: Максимальное время обработки запроса
            net_delay_min: Минимальная сетевая задержка
            net_delay_max: Максимальная сетевая задержка
            max_requests_in_flight: Максимальное количество одновременно обрабатываемых запросов
                                    (None = без ограничений)
            initial_nodes: Начальное количество узлов
            node_capacity: Пропускная способность каждого узла (количество одновременных запросов)
            max_wait_time: Максимальное время ожидания в очереди (None = без ограничений)
        """
        self.env = env
        self.lambda_rate = lambda_rate
        self.service_time_min = service_time_min
        self.service_time_max = service_time_max
        self.net_delay_min = net_delay_min
        self.net_delay_max = net_delay_max
        self.max_requests_in_flight = max_requests_in_flight
        self.node_capacity = node_capacity
        self.max_wait_time = max_wait_time
        
        # Очередь запросов (Store может иметь ограничение размера)
        queue_capacity = None if max_requests_in_flight is None else max_requests_in_flight * 10
        self.queue = simpy.Store(env, capacity=queue_capacity)
        
        # Ограничение на общее количество одновременно обрабатываемых запросов
        # Используем только для проверки переполнения очереди, не для ограничения обработки
        # Реальная пропускная способность определяется capacity каждого узла
        if max_requests_in_flight is not None:
            self.global_capacity = None  # Не используем для ограничения обработки
            self.max_requests_in_flight = max_requests_in_flight
        else:
            self.global_capacity = None
            self.max_requests_in_flight = None
        
        # Пул узлов обработки
        self.nodes: List[StorageNode] = []
        self.next_request_id = 0
        
        # Callback для логирования (инициализируем до вызова add_node)
        self.log_callback = None
        
        # Инициализация начальных узлов
        for i in range(initial_nodes):
            self.add_node()
        
        # Метрики
        self.processed_requests: List[Request] = []
        self.rejected_requests: List[Request] = []
        
        # Флаги управления
        self.is_running = False
        self.is_paused = False
        
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
    
    def add_node(self) -> StorageNode:
        """
        Добавляет новый узел в пул.
        
        Returns:
            Созданный узел
        """
        node_id = len(self.nodes)
        node = StorageNode(self.env, node_id, capacity=self.node_capacity)
        self.nodes.append(node)
        self._log(f"Добавлен узел #{node_id}. Всего узлов: {len(self.nodes)}", "INFO")
        return node
    
    def remove_node(self) -> bool:
        """
        Удаляет последний добавленный узел из пула.
        
        Returns:
            True если узел был удален, False если узлов недостаточно
        """
        if len(self.nodes) > 0:
            node = self.nodes.pop()
            node.is_active = False
            self._log(f"Удален узел #{node.node_id}. Всего узлов: {len(self.nodes)}", "INFO")
            return True
        return False
    
    def get_active_nodes(self) -> List[StorageNode]:
        """
        Возвращает список активных узлов.
        
        Returns:
            Список активных узлов
        """
        return [node for node in self.nodes if node.is_active]
    
    def get_queue_length(self) -> int:
        """
        Возвращает текущую длину очереди.
        
        Returns:
            Количество запросов в очереди
        """
        return len(self.queue.items)
    
    def generate_network_delay(self) -> float:
        """
        Генерирует случайную сетевую задержку.
        
        Returns:
            Случайная задержка в диапазоне [net_delay_min, net_delay_max]
        """
        if self.net_delay_max > self.net_delay_min:
            return np.random.uniform(self.net_delay_min, self.net_delay_max)
        return self.net_delay_min
    
    def generate_service_time(self) -> float:
        """
        Генерирует случайное время обработки запроса.
        
        Returns:
            Случайное время обработки в диапазоне [service_time_min, service_time_max]
        """
        return np.random.uniform(self.service_time_min, self.service_time_max)
    
    def generate_interarrival_time(self) -> float:
        """
        Генерирует межприходный интервал для экспоненциального потока.
        
        Returns:
            Случайный межприходный интервал
        """
        if self.lambda_rate > 0:
            return np.random.exponential(1.0 / self.lambda_rate)
        return float('inf')
    
    def request_generator(self):
        """
        Генератор входящих запросов.
        
        Создает запросы с экспоненциальным распределением межприходных интервалов
        и помещает их в очередь.
        """
        while self.is_running:
            if self.is_paused:
                yield self.env.timeout(0.1)
                continue
                
            # Генерация межприходного интервала
            interarrival = self.generate_interarrival_time()
            yield self.env.timeout(interarrival)
            
            if not self.is_running:
                break
            
            # Создание нового запроса
            request = Request(
                request_id=self.next_request_id,
                arrival_time=self.env.now
            )
            self.next_request_id += 1
            
            # Логируем каждые 50 запросов
            if request.request_id % 50 == 0:
                self._log(f"Сгенерировано запросов: {request.request_id}", "INFO")
            
            # Генерация времени обработки
            request.service_time = self.generate_service_time()
            
            # Проверка ограничения на максимальное количество запросов
            # Если очередь переполнена, отклоняем запрос сразу
            if self.max_requests_in_flight is not None:
                current_in_system = (
                    len(self.queue.items) +  # В очереди
                    sum(len(node.resource.users) for node in self.nodes)  # В обработке
                )
                if current_in_system >= self.max_requests_in_flight:
                    # Очередь переполнена - отклоняем запрос
                    request.rejected = True
                    request.rejected_reason = 'queue_full'
                    self.rejected_requests.append(request)
                    if len(self.rejected_requests) % 10 == 0:
                        self._log(
                            f"Запрос #{request.request_id} отклонен: переполнение очереди "
                            f"(в системе: {current_in_system}/{self.max_requests_in_flight})",
                            "WARNING"
                        )
                    continue
            
            # Попытка добавить запрос в очередь
            try:
                # Если очередь имеет ограничение размера, может быть отказ
                request.queue_entry_time = self.env.now
                yield self.queue.put(request)
            except (simpy.Interrupt, Exception) as e:
                # Очередь переполнена или другая ошибка
                request.rejected = True
                request.rejected_reason = 'queue_full'
                self.rejected_requests.append(request)
    
    def request_processor(self, load_balancer):
        """
        Обрабатывает запросы из очереди.
        Создает несколько параллельных процессов для обработки запросов.
        
        Args:
            load_balancer: Балансировщик нагрузки для выбора узла
        """
        # Создаем несколько параллельных процессов обработки
        # Количество процессов должно быть достаточным для использования всех узлов
        # Используем max_requests_in_flight или разумное значение по умолчанию
        if self.max_requests_in_flight is not None:
            max_parallel_processors = self.max_requests_in_flight
        else:
            # Без ограничений - создаем достаточно процессов для параллельной обработки
            max_parallel_processors = 100
        
        # Запускаем несколько параллельных обработчиков
        for _ in range(max_parallel_processors):
            self.env.process(self._single_request_processor(load_balancer))
        
        # Генератор должен что-то yield'ить, чтобы быть валидным
        while self.is_running:
            yield self.env.timeout(1.0)  # Просто ждем, процессы уже запущены
    
    def _single_request_processor(self, load_balancer):
        """
        Один процесс обработки запросов из очереди.
        
        Args:
            load_balancer: Балансировщик нагрузки для выбора узла
        """
        while self.is_running:
            if self.is_paused:
                yield self.env.timeout(0.1)
                continue
            
            try:
                # Получаем запрос из очереди
                request = yield self.queue.get()
                
                # Проверяем максимальное время ожидания в очереди
                if self.max_wait_time is not None and request.queue_entry_time is not None:
                    wait_time = self.env.now - request.queue_entry_time
                    if wait_time > self.max_wait_time:
                        # Превышено время ожидания - отклоняем запрос
                        request.rejected = True
                        request.rejected_reason = 'wait_timeout'
                        self.rejected_requests.append(request)
                        if len([r for r in self.rejected_requests if r.rejected_reason == 'wait_timeout']) % 10 == 0:
                            self._log(
                                f"Запрос #{request.request_id} отклонен: превышено время ожидания "
                                f"({wait_time:.2f} > {self.max_wait_time})",
                                "WARNING"
                            )
                        continue
                
                # Обрабатываем запрос
                # Ограничение параллелизма обеспечивается capacity каждого узла
                yield self.env.process(self._process_request(request, load_balancer))
                    
            except simpy.Interrupt:
                break
    
    def _process_request(self, request: Request, load_balancer):
        """
        Обрабатывает один запрос на выбранном узле.
        
        Args:
            request: Запрос для обработки
            load_balancer: Балансировщик нагрузки
        """
        # Выбираем узел через балансировщик
        node = load_balancer.select_node(self.get_active_nodes())
        
        if node is None:
            # Нет доступных узлов - отказ
            request.rejected = True
            request.rejected_reason = 'no_nodes'
            self.rejected_requests.append(request)
            return
        
        # Добавляем сетевую задержку
        net_delay = self.generate_network_delay()
        yield self.env.timeout(net_delay)
        
        # Обрабатываем запрос на узле (используем yield from для делегирования генератору)
        yield from node.process_request(request, request.service_time)
        
        # Запрос успешно обработан
        self.processed_requests.append(request)
        
        # Логируем каждые 50 обработанных запросов
        if len(self.processed_requests) % 50 == 0:
            response_time = request.get_response_time()
            self._log(
                f"Обработано запросов: {len(self.processed_requests)}. "
                f"Последний: запрос #{request.request_id} на узле #{node.node_id}, "
                f"время отклика: {response_time:.2f}",
                "INFO"
            )
    
    def get_system_state(self) -> Dict[str, Any]:
        """
        Возвращает текущее состояние системы.
        
        Returns:
            Словарь с текущими метриками системы
        """
        return {
            'sim_time': self.env.now,
            'queue_length': self.get_queue_length(),
            'active_nodes': len(self.get_active_nodes()),
            'total_nodes': len(self.nodes),
            'processed_count': len(self.processed_requests),
            'rejected_count': len(self.rejected_requests),
        }

