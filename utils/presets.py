# -*- coding: utf-8 -*-
"""
Пресеты настроек для экспериментов.

Содержит предустановленные конфигурации для различных сценариев моделирования.
"""

from typing import Dict, Any, List


class Preset:
    """Класс для представления пресета настроек."""
    
    def __init__(self, name: str, description: str, parameters: Dict[str, Any]):
        """
        Инициализирует пресет.
        
        Args:
            name: Название пресета
            description: Описание пресета и ожидаемого поведения
            parameters: Словарь с параметрами модели
        """
        self.name = name
        self.description = description
        self.parameters = parameters
    
    def get_parameters(self) -> Dict[str, Any]:
        """Возвращает параметры пресета."""
        return self.parameters.copy()


# Определение пресетов
PRESETS: List[Preset] = [
    Preset(
        name="Нормальная нагрузка, без масштабирования",
        description=(
            "Базовый кейс: система в нормальном режиме, ресурсов хватает, очередь небольшая. "
            "Это эталон для сравнения.\n\n"
            "Ожидание: почти нет очереди, отклонений ≈ 0, SLA высокий (80–100%)."
        ),
        parameters={
            'lambda_rate': 1.0,
            'service_time_min': 0.5,
            'service_time_max': 2.0,
            'net_delay_min': 0.0,
            'net_delay_max': 0.1,
            'max_requests_in_flight': 100,
            'min_nodes': 3,
            'max_nodes': 3,
            'initial_nodes': 3,
            'low_threshold': 0.0,
            'high_threshold': 999.0,
            'control_interval': 50.0,
            'scale_cooldown': 1000.0,
            'simulation_duration': 200.0,
            'sla_threshold': 5.0,
            'max_wait_time': 20.0,
        }
    ),
    Preset(
        name="Пиковая нагрузка без масштабирования",
        description=(
            "Перегрузка: показать, как система задыхается, если λ сильно вырастает, "
            "а узлов по-прежнему мало.\n\n"
            "Ожидание: очередь растёт, много отказов по таймауту/переполнению, "
            "среднее время отклика большое, SLA сильно падает. Это кейс «без регулирования»."
        ),
        parameters={
            'lambda_rate': 4.0,
            'service_time_min': 0.5,
            'service_time_max': 2.0,
            'net_delay_min': 0.0,
            'net_delay_max': 0.1,
            'max_requests_in_flight': 100,
            'min_nodes': 3,
            'max_nodes': 3,
            'initial_nodes': 3,
            'low_threshold': 0.0,
            'high_threshold': 999.0,
            'control_interval': 50.0,
            'scale_cooldown': 1000.0,
            'simulation_duration': 200.0,
            'sla_threshold': 5.0,
            'max_wait_time': 20.0,
        }
    ),
    Preset(
        name="Пиковая нагрузка с автомасштабированием",
        description=(
            "Главный демонстрационный кейс: те же λ и сервис, но включён autoscaling — "
            "сравниваешь с пресетом 2.\n\n"
            "Ожидание: в начале — перегрузка, очередь растёт → autoscaler увеличивает N "
            "до 6–10 узлов → очередь и отклик падают, число отказов снижается, SLA заметно "
            "лучше, чем в пресете 2."
        ),
        parameters={
            'lambda_rate': 4.0,
            'service_time_min': 0.5,
            'service_time_max': 2.0,
            'net_delay_min': 0.0,
            'net_delay_max': 0.1,
            'max_requests_in_flight': 100,
            'min_nodes': 2,
            'max_nodes': 10,
            'initial_nodes': 2,
            'low_threshold': 2.0,
            'high_threshold': 8.0,
            'control_interval': 5.0,
            'scale_cooldown': 10.0,
            'simulation_duration': 200.0,
            'sla_threshold': 5.0,
            'max_wait_time': 20.0,
        }
    ),
    Preset(
        name="Низкая нагрузка, экономия ресурсов",
        description=(
            "Показать, как при небольшом λ autoscaler может уменьшать количество узлов, "
            "сохраняя SLA, но экономя ресурсы.\n\n"
            "Ожидание: поначалу узлов много, очередь ≈ 0 → контроллер постепенно уменьшает "
            "число узлов до 1–2, при этом SLA остаётся почти 100%. Компромисс между затратами и качеством."
        ),
        parameters={
            'lambda_rate': 1.0,
            'service_time_min': 0.5,
            'service_time_max': 2.0,
            'net_delay_min': 0.0,
            'net_delay_max': 0.1,
            'max_requests_in_flight': 100,
            'min_nodes': 1,
            'max_nodes': 8,
            'initial_nodes': 5,
            'low_threshold': 1.0,
            'high_threshold': 4.0,
            'control_interval': 10.0,
            'scale_cooldown': 20.0,
            'simulation_duration': 200.0,
            'sla_threshold': 5.0,
            'max_wait_time': 20.0,
        }
    ),
    Preset(
        name="Плохая сеть (деградация канала)",
        description=(
            "Показать, что одних узлов мало, если сеть тормозит. Крутой кейс для раздела "
            "«ограничения модели».\n\n"
            "Ожидание: autoscaler добавляет узлы, но из-за больших сетевых задержек среднее "
            "время отклика всё равно высокое, SLA заметно хуже, чем в пресете 1–3. "
            "Демонстрация того, что «масштабирование серверов не лечит плохой канал»."
        ),
        parameters={
            'lambda_rate': 2.0,
            'service_time_min': 0.5,
            'service_time_max': 2.0,
            'net_delay_min': 5.0,
            'net_delay_max': 10.0,
            'max_requests_in_flight': 100,
            'min_nodes': 2,
            'max_nodes': 10,
            'initial_nodes': 3,
            'low_threshold': 2.0,
            'high_threshold': 8.0,
            'control_interval': 5.0,
            'scale_cooldown': 10.0,
            'simulation_duration': 200.0,
            'sla_threshold': 5.0,
            'max_wait_time': 20.0,
        }
    ),
    Preset(
        name="Высокий SLA (стабильная система)",
        description=(
            "Стабильная система с высоким SLA: оптимальные параметры для обеспечения "
            "высокого качества обслуживания.\n\n"
            "Ожидание: очередь маленькая (средняя длина 0–3), отказов почти нет, "
            "среднее время отклика заметно ниже 5, SLA% 80–95% (по хорошему прогону "
            "может и к 100% приблизиться)."
        ),
        parameters={
            'lambda_rate': 1.0,
            'service_time_min': 0.5,
            'service_time_max': 2.0,
            'net_delay_min': 0.0,
            'net_delay_max': 0.2,
            'max_requests_in_flight': 200,
            'min_nodes': 3,
            'max_nodes': 6,
            'initial_nodes': 3,
            'low_threshold': 2.0,
            'high_threshold': 5.0,
            'control_interval': 10.0,
            'scale_cooldown': 20.0,
            'simulation_duration': 300.0,
            'sla_threshold': 5.0,
            'max_wait_time': 20.0,
        }
    ),
]


def get_preset_by_name(name: str) -> Preset:
    """
    Получает пресет по имени.
    
    Args:
        name: Название пресета
        
    Returns:
        Preset объект или None, если не найден
    """
    for preset in PRESETS:
        if preset.name == name:
            return preset
    return None


def get_all_presets() -> List[Preset]:
    """Возвращает список всех пресетов."""
    return PRESETS.copy()

