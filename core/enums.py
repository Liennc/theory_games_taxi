"""Перечисления для статусов"""
from enum import Enum

class DriverStatus(Enum):
    FREE = "свободен"
    BUSY = "выполняет заказ"
    MOVING = "едет в зону"

class OrderStatus(Enum):
    PENDING = "ожидает водителя"
    ACCEPTED = "принят"
    COMPLETED = "завершен"
    CANCELLED = "отменен"