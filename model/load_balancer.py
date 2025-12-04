# -*- coding: utf-8 -*-
"""
Балансировщик нагрузки для распределения запросов по узлам.

Реализует алгоритм round-robin для равномерного распределения нагрузки.
"""

from typing import List, Optional
from .core import StorageNode, Request


class LoadBalancer:
    """
    Балансировщик нагрузки, распределяющий запросы по активным узлам.
    
    Использует алгоритм round-robin для равномерного распределения.
    """
    
    def __init__(self):
        """Инициализирует балансировщик нагрузки."""
        self.current_index = 0
    
    def select_node(self, nodes: List[StorageNode]) -> Optional[StorageNode]:
        """
        Выбирает узел для обработки запроса по алгоритму round-robin.
        
        Args:
            nodes: Список доступных узлов
            
        Returns:
            Выбранный узел или None, если узлов нет
        """
        if not nodes:
            return None
        
        # Фильтруем только активные узлы
        active_nodes = [node for node in nodes if node.is_active]
        if not active_nodes:
            return None
        
        # Round-robin: выбираем следующий узел по кругу
        selected = active_nodes[self.current_index % len(active_nodes)]
        self.current_index = (self.current_index + 1) % len(active_nodes)
        
        return selected
    
    def reset(self):
        """Сбрасывает состояние балансировщика."""
        self.current_index = 0

