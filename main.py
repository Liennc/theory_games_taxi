"""Главный файл для запуска симуляции"""
from core.simulation import CitySimulation
#from utils.visualization import visualize_simulation
#from utils.statistics import print_final_report

def main():
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
            # sim.debug_simulation()

            # Небольшая пауза для удобства чтения
            # import time

            # time.sleep(0.5)

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
            print(f"Процент выполнения: {completion_rate:.1f}%")

if __name__ == "__main__":
    main()
