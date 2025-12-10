"""
Этап 1: Базовые классы и структуры данных
"""

'''import numpy as np
import random
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import time


class DriverStatus(Enum):
    """Статусы водителя"""
    FREE = "свободен"
    BUSY = "выполняет заказ"
    MOVING = "едет в зону"


class OrderStatus(Enum):
    """Статусы заказа"""
    PENDING = "ожидает водителя"
    ACCEPTED = "принят"
    COMPLETED = "завершен"
    CANCELLED = "отменен"


@dataclass
class Zone:
    """
    Класс, представляющий зону города

    Attributes:
        id: Уникальный идентификатор зоны
        name: Название зоны
        base_demand_rate: Базовая интенсивность спроса (заказов в минуту)
        base_price_multiplier: Базовый множитель тарифа
        surge_multiplier: Текущий динамический множитель цены
        travel_time_matrix: Время перемещения в другие зоны (в минутах)
        color: Цвет для визуализации
    """

    id: int
    name: str
    base_demand_rate: float
    base_price_multiplier: float = 1.0
    surge_multiplier: float = 1.0
    travel_time_matrix: Dict[str, float] = None
    color: str = "white"

    def __post_init__(self):
        """Инициализация после создания объекта"""
        if self.travel_time_matrix is None:
            self.travel_time_matrix = {}

    def get_travel_time_to(self, target_zone: 'Zone') -> float:
        """
        Получить время перемещения в другую зону

        Args:
            target_zone: Целевая зона

        Returns:
            Время в минутах
        """
        key = f"{self.name}->{target_zone.name}"
        return self.travel_time_matrix.get(key, 10.0)  # Значение по умолчанию

    def calculate_order_price(self, destination_zone: 'Zone', base_fare: float = 5.0) -> float:
        """
        Рассчитать стоимость заказа

        Args:
            destination_zone: Зона назначения
            base_fare: Базовая стоимость

        Returns:
            Стоимость поездки
        """
        distance_factor = self.get_travel_time_to(destination_zone) / 10.0
        price = (base_fare * distance_factor *
                 self.base_price_multiplier *
                 self.surge_multiplier)
        return round(price, 2)

    def update_surge_multiplier(self, demand_supply_ratio: float) -> None:
        """
        Обновить динамический множитель цены

        Args:
            demand_supply_ratio: Соотношение спроса и предложения
        """
        # Простая модель динамического ценообразования
        if demand_supply_ratio > 1.5:
            self.surge_multiplier = min(3.0, self.surge_multiplier * 1.2)
        elif demand_supply_ratio > 1.2:
            self.surge_multiplier = min(2.5, self.surge_multiplier * 1.1)
        elif demand_supply_ratio < 0.8:
            self.surge_multiplier = max(0.7, self.surge_multiplier * 0.95)
        elif demand_supply_ratio < 0.5:
            self.surge_multiplier = max(0.5, self.surge_multiplier * 0.9)
        else:
            # Плавное возвращение к 1.0
            if self.surge_multiplier > 1.0:
                self.surge_multiplier = max(1.0, self.surge_multiplier * 0.98)
            elif self.surge_multiplier < 1.0:
                self.surge_multiplier = min(1.0, self.surge_multiplier * 1.02)

    def generate_demand(self, time_interval: float = 1.0) -> int:
        """
        Сгенерировать количество заказов за интервал времени

        Args:
            time_interval: Интервал времени в минутах

        Returns:
            Количество новых заказов
        """
        # БАЗОВЫЙ спрос уменьшается при высоких ценах!
        # Чем выше цена (surge_multiplier), тем меньше спрос
        effective_demand_rate = self.base_demand_rate / max(1.0, self.surge_multiplier ** 0.7)

        # Распределение Пуассона для генерации заказов
        expected_orders = effective_demand_rate * time_interval

        # Упрощенная реализация распределения Пуассона
        orders = 0
        L = 2.718281828459045 ** (-expected_orders)  # e^(-λ)
        p = 1.0

        while p > L:
            orders += 1
            p *= random.random()

        return orders - 1

    def __str__(self) -> str:
        return f"Зона '{self.name}' (спрос: {self.base_demand_rate}/мин, цена: x{self.surge_multiplier:.2f})"

    def __hash__(self):
        # Используем id для хеширования
        return hash(self.id)

    def __eq__(self, other):
        # Сравниваем по id
        if isinstance(other, Zone):
            return self.id == other.id
        return False


@dataclass
class Driver:
    """
    Класс, представляющий водителя

    Attributes:
        id: Уникальный идентификатор водителя
        name: Имя водителя
        current_zone: Текущая зона
        status: Текущий статус
        total_earnings: Общий заработок
        strategy_params: Параметры стратегии
        current_order: Текущий заказ
        time_to_complete: Время до завершения текущего действия
        satisfaction: Уровень удовлетворенности (0-100)
        color: Цвет для визуализации
    """

    id: int
    name: str
    current_zone: Zone
    status: DriverStatus = DriverStatus.FREE
    total_earnings: float = 0.0
    strategy_params: Dict = None
    current_order: Optional['Order'] = None
    time_to_complete: float = 0.0
    satisfaction: float = 100.0
    color: str = "blue"
    simulation: Optional['CitySimulation'] = None

    def calculate_expected_order_profit(self, order: 'Order') -> float:
        """
        Рассчитать ожидаемую прибыль от конкретного заказа
        """
        # 1. Доход от заказа
        order_income = order.price

        # 2. Стоимость подачи машины (если не в той же зоне)
        if self.current_zone != order.start_zone:
            pickup_time = self.current_zone.get_travel_time_to(order.start_zone)
            pickup_cost = pickup_time * self.cost_per_minute
        else:
            pickup_time = random.uniform(2, 5)  # 2-5 минут в той же зоне
            pickup_cost = pickup_time * self.cost_per_minute

        # 3. Стоимость выполнения поездки
        trip_time = order.estimated_duration
        trip_cost = trip_time * self.cost_per_minute

        # 4. Альтернативная стоимость времени
        # (время, которое можно было бы потратить на другой заказ)
        opportunity_cost = (pickup_time + trip_time) * self.time_value_per_minute

        # 5. Общая прибыль
        total_profit = order_income - pickup_cost - trip_cost - opportunity_cost

        return total_profit

    def __post_init__(self):
        # Добавляем параметры стоимости
        if self.strategy_params is None:
            self.strategy_params = {
                "min_profit_threshold": 3.0,
                "risk_tolerance": 0.5,
                "exploration_rate": 0.1,
                "patience": 0.8,
                "cost_per_minute": 0.2,  # Стоимость минуты (бензин, амортизация)
                "time_value_per_minute": 0.1,  # Ценность времени водителя
            }

        self.cost_per_minute = self.strategy_params.get("cost_per_minute", 0.2)
        self.time_value_per_minute = self.strategy_params.get("time_value_per_minute", 0.1)

    def calculate_order_profit(self, order: 'Order', cost_per_minute: float = 0.2) -> float:
        """
        Рассчитать прибыль от заказа

        Args:
            order: Заказ для оценки
            cost_per_minute: Стоимость в минуту (бензин, амортизация)

        Returns:
            Ожидаемая прибыль
        """
        travel_time = self.current_zone.get_travel_time_to(order.start_zone)
        trip_time = order.estimated_duration

        # Расходы: перемещение к клиенту + поездка
        total_cost = (travel_time + trip_time) * cost_per_minute

        # Прибыль
        profit = order.price - total_cost

        return profit

    def calculate_expected_profit_in_zone(self, zone: Zone, drivers_count: int,
                                          available_orders: List['Order'],
                                          travel_cost: bool = False) -> float:
        """
        Рассчитать ожидаемый доход в зоне

        Args:
            zone: Целевая зона
            drivers_count: Количество водителей в зоне
            available_orders: Доступные заказы в зоне
            travel_cost: Учитывать ли стоимость перемещения в зону
        """
        total_expected_profit = 0.0

        # Если есть доступные заказы
        if available_orders:
            # Вероятность получить конкретный заказ
            # Чем больше водителей, тем меньше вероятность
            probability_per_order = 1.0 / max(1, drivers_count + 1)

            # Считаем ожидаемый доход от каждого заказа
            for order in available_orders:
                profit = self.calculate_expected_order_profit(order)
                if travel_cost:
                    # Вычитаем стоимость перемещения в зону
                    travel_time = self.current_zone.get_travel_time_to(zone)
                    travel_cost_amount = travel_time * self.cost_per_minute
                    profit -= travel_cost_amount

                total_expected_profit += probability_per_order * profit

        # Если нет доступных заказов, считаем ожидаемый доход от будущих заказов
        else:
            # Ожидаемое количество заказов в минуту
            expected_orders_per_minute = zone.base_demand_rate / max(1.0, zone.surge_multiplier)

            # Средняя стоимость заказа в зоне (это можно уточнить)
            avg_order_price = 20.0 * zone.base_price_multiplier * zone.surge_multiplier

            # Ожидаемый доход в минуту
            expected_profit_per_minute = (expected_orders_per_minute * avg_order_price) / max(1, drivers_count + 1)

            # Минус стоимость ожидания
            waiting_cost_per_minute = self.cost_per_minute + self.time_value_per_minute

            total_expected_profit = expected_profit_per_minute - waiting_cost_per_minute

            if travel_cost:
                travel_time = self.current_zone.get_travel_time_to(zone)
                travel_cost_amount = travel_time * self.cost_per_minute
                total_expected_profit -= travel_cost_amount

        return total_expected_profit

    def decide_on_order(self, order: 'Order') -> bool:
        """
        Принять решение о принятии заказа

        Args:
            order: Предлагаемый заказ

        Returns:
            True если водитель принимает заказ
        """
        if self.status != DriverStatus.FREE:
            return False

        profit = self.calculate_expected_order_profit(order)
        min_threshold = self.strategy_params["min_profit_threshold"]

        # Учитываем уровень удовлетворенности
        threshold_adjustment = 1.0 - (100 - self.satisfaction) / 200
        effective_threshold = min_threshold * threshold_adjustment

        # С вероятностью, зависящей от терпения, принимаем заказы с меньшей прибылью
        if profit < effective_threshold and random.random() > self.strategy_params["patience"]:
            return False

        return profit >= effective_threshold

    def decide_zone_move(self, zones: List[Zone],
                         drivers_in_zones: Dict[int, int],
                         available_orders_by_zone: Dict[int, List['Order']]) -> Optional[Zone]:
        """
        Принять решение о перемещении в другую зону

        Args:
            zones: Список доступных зон
            drivers_in_zones: Количество водителей в каждой зоне (ключ - zone.id)
            available_orders_by_zone: Заказы доступные в каждой зоне

        Returns:
            Зона для перемещения или None если остаться
        """
        if self.status != DriverStatus.FREE:
            return None

        # Эпсилон-жадная стратегия
        if random.random() < self.strategy_params["exploration_rate"]:
            # Исследование: выбираем случайную зону
            target_zone = random.choice(zones)
            if target_zone != self.current_zone:
                return target_zone
            return None

        # Эксплуатация: выбираем зону с максимальным ожидаемым доходом
        best_zone = None
        best_expected_profit = -float('inf')

        # Для зоны считаем доход от доступных заказов
        for zone in zones:
            expected_profit = self.calculate_expected_profit_in_zone(
                    zone, drivers_in_zones.get(zone.id, 0),
                available_orders_by_zone.get(zone.id, []),
                travel_cost = (zone != self.current_zone)  # Учитываем в текущей зоне или нет для расчета стоимости перемещения
            )




            if expected_profit > best_expected_profit:
                best_expected_profit = expected_profit
                best_zone = zone

        # Перемещаемся только если ожидаемая прибыль значительно выше
        if best_zone and best_zone != self.current_zone and best_expected_profit > 5.0:
            return best_zone

        return None

    def start_moving(self, target_zone: Zone) -> None:
        """Начать перемещение в другую зону"""
        self.status = DriverStatus.MOVING
        travel_time = self.current_zone.get_travel_time_to(target_zone)
        self.time_to_complete = travel_time
        # Обновляем удовлетворенность (перемещение снижает удовлетворенность)
        self.satisfaction = max(0, self.satisfaction - 5)

    def start_order(self, order: 'Order') -> None:
        """Начать выполнение заказа"""
        print(f"DEBUG_START_ORDER: {self.name} начинает заказ #{order.id}")

        self.status = DriverStatus.BUSY

        # Время на подачу (от 1 до 5 минут если в той же зоне)
        if self.current_zone == order.start_zone:
            pickup_time = random.uniform(1, 5)
        else:
            pickup_time = self.current_zone.get_travel_time_to(order.start_zone)

        # ОБЩЕЕ время = подача + поездка
        total_time = pickup_time + order.estimated_duration

        self.current_order = order
        self.time_to_complete = total_time
        order.status = OrderStatus.ACCEPTED

        print(f"DEBUG_START_ORDER: pickup_time={pickup_time:.1f}, "
              f"trip={order.estimated_duration:.1f}, total={total_time:.1f}")

        self.satisfaction = min(100, self.satisfaction + 10)

    def complete_current_action(self) -> None:
        """Завершить текущее действие (поездку или заказ)"""
        #print(f"DEBUG_COMPLETE: {self.name} начинает завершение, статус={self.status.value}")

        if self.status == DriverStatus.MOVING:
            #print(f"DEBUG_COMPLETE: {self.name} прибыл в зону")
            self.status = DriverStatus.FREE
            self.time_to_complete = 0.0
            self.satisfaction = min(100, self.satisfaction + 3)

        elif self.status == DriverStatus.BUSY and self.current_order:
            #print(f"DEBUG_COMPLETE: {self.name} завершает заказ #{self.current_order.id}")
            #print(f"DEBUG_COMPLETE: Заработок до: {self.total_earnings}")

            # Завершаем заказ
            self.status = DriverStatus.FREE
            self.total_earnings += self.current_order.price
            self.current_order.status = OrderStatus.COMPLETED
            self.current_zone = self.current_order.end_zone
            self.current_order = None
            self.time_to_complete = 0.0
            self.satisfaction = min(100, self.satisfaction + 15)

            print(f"DEBUG_COMPLETE: Заработок после: {self.total_earnings}")
            print(f"DEBUG_COMPLETE: Новый статус: {self.status.value}")
        else:
            print(f"DEBUG_COMPLETE: {self.name} статус {self.status.value}, current_order={self.current_order}")

    def update(self, time_elapsed: float = 1.0) -> None:
        """
        Обновить состояние водителя
        """
        #print(f"DEBUG_UPDATE: {self.name} статус={self.status.value}, "
              #f"time_to_complete={self.time_to_complete}, "
              #f"time_elapsed={time_elapsed}")

        if self.status in [DriverStatus.MOVING, DriverStatus.BUSY]:
            old_time = self.time_to_complete
            self.time_to_complete -= time_elapsed
            #print(f"DEBUG_UPDATE: {self.name} {old_time:.1f} -> {self.time_to_complete:.1f}")

            if self.time_to_complete <= 0:
                #print(f"DEBUG_UPDATE: {self.name} завершает действие!")
                self.complete_current_action()
            #else:
                #print(f"DEBUG_UPDATE: {self.name} еще ждет {self.time_to_complete:.1f} мин")

        # Постепенное снижение удовлетворенности при бездействии
        if self.status == DriverStatus.FREE:
            self.satisfaction = max(0, self.satisfaction - 0.5)
    def __str__(self) -> str:
        status_str = f"{self.status.value}"
        if self.current_order:
            status_str += f" (заказ #{self.current_order.id})"
        return (f"Водитель {self.name} [{self.id}]: {status_str}, "
                f"зона: {self.current_zone.name}, "
                f"заработал: {self.total_earnings:.2f}, "
                f"удовлетворенность: {self.satisfaction:.1f}")

    def get_time_to_pickup(self, order: 'Order') -> float:
        """
        Получить время чтобы доехать до клиента
        """
        if self.current_zone == order.start_zone:
            # Уже в той же зоне - 2-5 минут
            return random.uniform(2, 5)
        else:
            # Нужно ехать в другую зону
            return self.current_zone.get_travel_time_to(order.start_zone)

    def complete_current_action(self) -> None:
        """Завершить текущее действие (поездку или заказ)"""
        if self.status == DriverStatus.MOVING:
            self.status = DriverStatus.FREE
            self.time_to_complete = 0.0
            self.satisfaction = min(100, self.satisfaction + 3)

        elif self.status == DriverStatus.BUSY and self.current_order:
            # ЗАПОМИНАЕМ ЧТО ЗАКАЗ ЗАВЕРШЕН В ЭТУ МИНУТУ
            if hasattr(self, '_simulation'):  # Если есть ссылка на симуляцию
                self._simulation.orders_completed_this_minute += 1

            # Завершаем заказ
            self.status = DriverStatus.FREE
            self.total_earnings += self.current_order.price
            self.current_order.status = OrderStatus.COMPLETED
            self.current_zone = self.current_order.end_zone
            self.current_order = None
            self.time_to_complete = 0.0
            self.satisfaction = min(100, self.satisfaction + 15)

@dataclass
class Order:
    """
    Класс, представляющий заказ

    Attributes:
        id: Уникальный идентификатор заказа
        start_zone: Зона подачи
        end_zone: Зона назначения
        price: Стоимость поездки
        status: Текущий статус
        created_time: Время создания
        estimated_duration: Оценочная длительность поездки
        waiting_time: Время ожидания водителя
    """

    id: int
    start_zone: Zone
    end_zone: Zone
    price: float
    status: OrderStatus = OrderStatus.PENDING
    created_time: float = None
    estimated_duration: float = None
    waiting_time: float = 0.0

    def __post_init__(self):
        """Инициализация после создания объекта"""
        if self.estimated_duration is None:
            base_time = self.start_zone.get_travel_time_to(self.end_zone)
            #print(f"DEBUG_ORDER: Заказ {self.id} base_time={base_time}")

            # МИНИМУМ 10 минут, МАКСИМУМ 40 минут
            min_trip_time = max(10, min(40, base_time))

            # Логнормальное распределение
            mu = np.log(min_trip_time)
            sigma = 0.3

            normal_sample = np.random.normal(mu, sigma)
            self.estimated_duration = max(5, min(60, np.exp(normal_sample)))

            #print(f"DEBUG_ORDER: estimated_duration={self.estimated_duration:.1f}")

    def update(self, time_elapsed: float = 1.0) -> None:
        """
        Обновить состояние заказа
        """
        if self.status == OrderStatus.PENDING:
            self.waiting_time += time_elapsed
            # Отменяем заказ ЧЕРЕЗ 2 МИНУТЫ максимум
            if self.waiting_time > 2:  # Было 3, стало 2
                #print(f"DEBUG_ORDER_CANCEL: Заказ #{self.id} отменен (ждал {self.waiting_time} мин)")
                self.status = OrderStatus.CANCELLED

    def __str__(self) -> str:
        return (f"Заказ #{self.id}: {self.start_zone.name} → {self.end_zone.name}, "
                f"цена: {self.price:.2f}, статус: {self.status.value}")


class CitySimulation:
    """
    Основной класс симуляции города
    """

    def __init__(self):
        """Инициализация симуляции"""
        self.zones: Dict[int, Zone] = {}
        self.drivers: Dict[int, Driver] = {}
        self.orders: Dict[int, Order] = {}
        self.time: float = 0.0
        self.order_counter: int = 0
        self.driver_counter: int = 0

        # Создаем зоны города
        self._initialize_zones()

        # Создаем водителей
        self._initialize_drivers()
        # Счетчики за текущую минуту
        self.orders_completed_this_minute = 0
        self.orders_cancelled_this_minute = 0
        self.orders_created_this_minute = 0
        # Общие счетчики
        self.total_created_orders = 0
        self.total_completed_orders = 0
        self.total_cancelled_orders = 0
        # История по минутам
        self.minute_history = []  # Будем хранить статистику по каждой минуте

    def _initialize_zones(self) -> None:
        """Инициализация зон города"""
        # Матрица времени перемещения между зонами (в минутах)
        travel_times = {
            "Центр->Центр": 5,
            "Центр->Спальный район": 15,
            "Центр->Периферия": 25,
            "Спальный район->Центр": 20,
            "Спальный район->Спальный район": 8,
            "Спальный район->Периферия": 18,
            "Периферия->Центр": 30,
            "Периферия->Спальный район": 22,
            "Периферия->Периферия": 12,
        }

        # Создаем зоны
        self.zones[1] = Zone(
            id=1,
            name="Центр",
            base_demand_rate=2.0,  # БЫЛО 10.0, СТАЛО 2.0 (2 заказа в минуту)
            base_price_multiplier=1.2,
            surge_multiplier=1.0,
            travel_time_matrix=travel_times,
            color="red"
        )

        self.zones[2] = Zone(
            id=2,
            name="Спальный район",
            base_demand_rate=0.8,  # БЫЛО 4.0, СТАЛО 0.8
            base_price_multiplier=1.0,
            surge_multiplier=1.0,
            travel_time_matrix=travel_times,
            color="green"
        )

        self.zones[3] = Zone(
            id=3,
            name="Периферия",
            base_demand_rate=0.3,  # БЫЛО 1.5, СТАЛО 0.3
            base_price_multiplier=0.8,
            surge_multiplier=1.0,
            travel_time_matrix=travel_times,
            color="blue"
        )

    def _initialize_drivers(self) -> None:
        """Инициализация водителей"""
        driver_names = ["Иван", "Алексей", "Сергей", "Дмитрий", "Михаил",
                        "Андрей", "Александр", "Владимир", "Павел", "Николай",
                        "Олег", "Юрий", "Борис", "Григорий", "Василий",
                        "Константин", "Станислав", "Артем", "Тимофей", "Роман"]

        # Создаем 15 водителей вместо 8
        for i, name in enumerate(driver_names[:15]):
            zone_id = (i % 3) + 1
            self.driver_counter += 1
            self.drivers[self.driver_counter] = Driver(
                id=self.driver_counter,
                name=name,
                current_zone=self.zones[zone_id],
                simulation=self,
                color=f"#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}"
            )

    def generate_orders(self) -> None:
        """Генерация новых заказов"""
        # Не генерируем новые заказы, если уже много ожидающих
        pending_count = len([o for o in self.orders.values()
                             if o.status == OrderStatus.PENDING])

        if pending_count > 20:  # Максимум 20 ожидающих заказов
            return

        for zone in self.zones.values():
            num_orders = zone.generate_demand()
            self.total_created_orders += num_orders

            for _ in range(num_orders):
                self.order_counter += 1

                # Выбираем случайную зону назначения
                end_zone = random.choice(list(self.zones.values()))

                # Рассчитываем цену
                price = zone.calculate_order_price(end_zone)

                # Создаем заказ
                order = Order(
                    id=self.order_counter,
                    start_zone=zone,
                    end_zone=end_zone,
                    price=price
                )

                self.orders[self.order_counter] = order

    def match_orders_to_drivers(self) -> None:
        """Сопоставление заказов со свободными водителями"""
        pending_orders = [o for o in self.orders.values()
                          if o.status == OrderStatus.PENDING]

        free_drivers = [d for d in self.drivers.values()
                        if d.status == DriverStatus.FREE]

        for order in pending_orders:
            # Ищем свободных водителей в той же зоне
            zone_drivers = [d for d in free_drivers
                            if d.current_zone == order.start_zone]

            for driver in zone_drivers:
                if driver.decide_on_order(order):
                    driver.start_order(order)
                    free_drivers.remove(driver)
                    # print(f"{driver.name} принял {order}")
                    break

    def update_drivers_movement(self) -> None:
        """Обновление перемещения водителей"""
        # Считаем количество водителей в каждой зоне
        drivers_per_zone = {}
        available_orders_by_zone = {}

        for zone in self.zones.values():
            drivers_count = len([d for d in self.drivers.values()
                                 if d.current_zone == zone and
                                 d.status == DriverStatus.FREE])
            drivers_per_zone[zone] = drivers_count

            # Собираем доступные заказы в зоне
            zone_orders = [o for o in self.orders.values()
                           if o.start_zone == zone and
                           o.status == OrderStatus.PENDING]
            available_orders_by_zone[zone.id] = zone_orders

        # Каждый свободный водитель решает, перемещаться ли
        for driver in self.drivers.values():
            if driver.status == DriverStatus.FREE:
                target_zone = driver.decide_zone_move(
                    list(self.zones.values()),
                    drivers_per_zone,
                    available_orders_by_zone  # ← Передаем доступные заказы
                )

                if target_zone and target_zone != driver.current_zone:
                    driver.start_moving(target_zone)
                    # print(f"{driver.name} едет из {driver.current_zone.name} в {target_zone.name}")

    def update_surge_pricing(self) -> None:
        """Обновление динамического ценообразования"""
        for zone in self.zones.values():
            # Считаем количество свободных водителей в зоне
            free_drivers = len([d for d in self.drivers.values()
                                if d.current_zone == zone and
                                d.status == DriverStatus.FREE])

            # Рассчитываем соотношение спроса и предложения
            demand = zone.base_demand_rate * zone.surge_multiplier
            supply = max(1, free_drivers)
            ratio = demand / supply

            # Обновляем множитель цены
            zone.update_surge_multiplier(ratio)

    def cleanup_completed_orders(self) -> None:
        completed_ids = []
        for order_id, order in self.orders.items():
            if order.status == OrderStatus.COMPLETED:
                self.total_completed_orders += 1  # ← Считаем выполненные
                completed_ids.append(order_id)
            elif order.status == OrderStatus.CANCELLED:
                self.total_cancelled_orders += 1  # ← Считаем отмененные
                completed_ids.append(order_id)

        for order_id in completed_ids:
            del self.orders[order_id]
    def run_iteration(self, time_step: float = 1.0) -> None:
        """
        Выполнить одну итерацию симуляции (1 минута)
        """
        # ОБНУЛЯЕМ счетчики на начало минуты
        self.orders_completed_this_minute = 0
        self.orders_cancelled_this_minute = 0
        self.orders_created_this_minute = 0

        # 1. Обновляем состояние водителей
        for driver in self.drivers.values():
            # Запоминаем статус до обновления
            was_busy = (driver.status == DriverStatus.BUSY)
            had_order = driver.current_order is not None

            # Обновляем водителя
            driver.update(time_step)

            # ПРОВЕРЯЕМ ЗАВЕРШИЛСЯ ЛИ ЗАКАЗ
            if was_busy and driver.status == DriverStatus.FREE and had_order:
                self.orders_completed_this_minute += 1

        # 2. Обновляем состояние заказов
        cancelled_this_minute = 0
        for order in self.orders.values():
            old_status = order.status
            order.update(time_step)
            if old_status == OrderStatus.PENDING and order.status == OrderStatus.CANCELLED:
                cancelled_this_minute += 1

        self.orders_cancelled_this_minute = cancelled_this_minute

        # 3. Генерируем новые заказы
        orders_before = len(self.orders)
        self.generate_orders()
        orders_after = len(self.orders)
        self.orders_created_this_minute = orders_after - orders_before

        # 4. Сопоставляем заказы с водителями
        self.match_orders_to_drivers()

        # 5. Обновляем перемещение водителей
        self.update_drivers_movement()

        # 6. Обновляем динамическое ценообразование
        self.update_surge_pricing()

        # 7. Очищаем завершенные заказы
        self.cleanup_completed_orders()

        # 9. Обновляем время
        self.time += time_step

    def get_statistics(self) -> Dict:
        """Получить статистику по симуляции"""
        total_earnings = sum(d.total_earnings for d in self.drivers.values())
        avg_earnings = total_earnings / len(self.drivers) if self.drivers else 0

        # Считаем заказы по статусам
        order_stats = {
            "pending": 0,
            "accepted": 0,
            "completed": 0,
            "cancelled": 0
        }

        for order in self.orders.values():
            if order.status == OrderStatus.PENDING:
                order_stats["pending"] += 1
            elif order.status == OrderStatus.ACCEPTED:
                order_stats["accepted"] += 1
            elif order.status == OrderStatus.COMPLETED:
                order_stats["completed"] += 1
            elif order.status == OrderStatus.CANCELLED:
                order_stats["cancelled"] += 1

        # Активные = ожидающие + принятые
        active_orders = order_stats["pending"] + order_stats["accepted"]

        # Статусы водителей
        free_drivers = len([d for d in self.drivers.values()
                            if d.status == DriverStatus.FREE])
        busy_drivers = len([d for d in self.drivers.values()
                            if d.status == DriverStatus.BUSY])
        moving_drivers = len([d for d in self.drivers.values()
                              if d.status == DriverStatus.MOVING])

        avg_satisfaction = (sum(d.satisfaction for d in self.drivers.values()) /
                            len(self.drivers) if self.drivers else 0)

        return {
            "time": self.time,
            "total_drivers": len(self.drivers),
            "free_drivers": free_drivers,
            "busy_drivers": busy_drivers,
            "moving_drivers": moving_drivers,

            # КЛЮЧЕВОЕ ИЗМЕНЕНИЕ:
            "active_orders": active_orders,  # Активные заказы
            "pending_orders": order_stats["pending"],  # Ожидают водителя
            "accepted_orders": order_stats["accepted"],  # Выполняются
            "completed_orders": order_stats["completed"],  # Завершены
            "cancelled_orders": order_stats["cancelled"],  # Отменены
            "total_orders_in_system": len(self.orders),  # Все в системе

            "total_earnings": total_earnings,
            "avg_earnings": avg_earnings,
            "avg_satisfaction": avg_satisfaction,

            "zone_stats": {
                zone.name: {
                    "surge_multiplier": zone.surge_multiplier,
                    "drivers_count": len([d for d in self.drivers.values()
                                          if d.current_zone == zone])
                }
                for zone in self.zones.values()
            }
        }

    def print_status(self) -> None:
        """Вывести текущий статус симуляции"""
        stats = self.get_statistics()

        print(f"\n=== Время: {stats['time']:.1f} мин ===")
        print(f"Водители: {stats['total_drivers']} всего, "
              f"{stats['free_drivers']} свободны, "
              f"{stats['busy_drivers']} заняты, "
              f"{stats['moving_drivers']} в пути")

        # НОВЫЙ ФОРМАТ:
        print(f"Заказы: {stats['active_orders']} активных "
              f"({stats['pending_orders']} ожидают, {stats['accepted_orders']} выполняются)")
        print(f"   📈 Создано новых заказов: {self.orders_created_this_minute}")
        print(f"   ✅ Выполнено заказов: {self.orders_completed_this_minute}")
        print(f"   ❌ Отменено заказов: {self.orders_cancelled_this_minute}")

        print(f"Всего заказов в системе: {stats['total_orders_in_system']}")

        print(f"Заработок: всего {stats['total_earnings']:.2f}, "
              f"в среднем {stats['avg_earnings']:.2f}")
        print(f"Удовлетворенность водителей: {stats['avg_satisfaction']:.1f}")

        print("\nСтатистика по зонам:")
        for zone_name, zone_stats in stats['zone_stats'].items():
            print(f"  {zone_name}: множитель цены x{zone_stats['surge_multiplier']:.2f}, "
                  f"водителей: {zone_stats['drivers_count']}")

    def debug_simulation(self):
        """Вывод отладочной информации"""
        print("\n" + "=" * 60)
        print("ОТЛАДОЧНАЯ ИНФОРМАЦИЯ:")
        print("=" * 60)

        # 1. Водителиf
        print("\n📋 ВОДИТЕЛИ:")
        for driver in self.drivers.values():
            status_info = f"{driver.status.value}"
            if driver.status == DriverStatus.BUSY:
                status_info += f" (осталось {driver.time_to_complete:.1f} мин)"
            elif driver.status == DriverStatus.MOVING:
                status_info += f" в {driver.current_zone.name} (осталось {driver.time_to_complete:.1f} мин)"

            print(f"  {driver.name}: {status_info}, заработок: {driver.total_earnings:.1f}")

        # 2. Заказы
        print("\n📋 ЗАКАЗЫ:")
        order_types = {"ожидает": 0, "выполняется": 0, "завершен": 0, "отменен": 0}

        for order in self.orders.values():
            if order.status == OrderStatus.PENDING:
                order_types["ожидает"] += 1
                print(f"  ⏳ #{order.id}: {order.start_zone.name}->{order.end_zone.name}, "
                      f"цена: {order.price:.1f}, ждет: {order.waiting_time:.1f} мин")
            elif order.status == OrderStatus.ACCEPTED:
                order_types["выполняется"] += 1
                # Найдем водителя
                driver_name = "?"
                for d in self.drivers.values():
                    if d.current_order and d.current_order.id == order.id:
                        driver_name = d.name
                        break
                print(f"  🚗 #{order.id}: {order.start_zone.name}->{order.end_zone.name}, "
                      f"водитель: {driver_name}, длительность: {order.estimated_duration:.1f} мин")
            elif order.status == OrderStatus.COMPLETED:
                order_types["завершен"] += 1
            elif order.status == OrderStatus.CANCELLED:
                order_types["отменен"] += 1

        print(f"\n📊 Сводка: {order_types}")

        # 3. Зоны
        print("\n📋 ЗОНЫ:")
        for zone in self.zones.values():
            drivers_in_zone = len([d for d in self.drivers.values()
                                   if d.current_zone == zone])
            free_in_zone = len([d for d in self.drivers.values()
                                if d.current_zone == zone and d.status == DriverStatus.FREE])
            print(f"  {zone.name}: {drivers_in_zone} водителей ({free_in_zone} свободно), "
                  f"множитель цены: x{zone.surge_multiplier:.2f}")


# Пример использования
if __name__ == "__main__":
    # Инициализация симуляции
    print("Инициализация симуляции города...")
    sim = CitySimulation()

    # Запускаем несколько итераций
    minutes = 50
    print(f"\nЗапуск симуляции на {minutes} минут...")
    for i in range(minutes):
        print(f"\n--- Минута {i + 1} ---")
        sim.run_iteration()
        sim.print_status()
        #sim.debug_simulation()

        # Небольшая пауза для удобства чтения
        #import time

        #time.sleep(0.5)

    print("\n=== Итоги симуляции ===")
    stats = sim.get_statistics()
    print(f"Всего времени: {stats['time']} минут")
    print(f"Общий заработок всех водителей: {stats['total_earnings']:.2f}")
    print(f"Средний заработок на водителя: {stats['avg_earnings']:.2f}")

    # Выводим информацию по каждому водителю
    print("\nИнформация по водителям:")
    for driver in sim.drivers.values():
        print(f"  {driver.name}: {driver.total_earnings:.2f}, "
              f"удовлетворенность: {driver.satisfaction:.1f}")

    print(f"\nВсего создано заказов: {sim.total_created_orders}")
    print(f"Всего выполнено заказов: {sim.total_completed_orders}")
    print(f"Всего отменено заказов: {sim.total_cancelled_orders}")

    if sim.total_created_orders > 0:
        completion_rate = (sim.total_completed_orders / sim.total_created_orders) * 100
        print(f"Процент выполнения: {completion_rate:.1f}%")'''