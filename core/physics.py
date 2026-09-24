from typing import List
from .models import Truck, Cargo, CalculateResult, AxleGroupResult


def calculate_loads(truck: Truck, cargos: List[Cargo]) -> CalculateResult:
    """
    Рассчитывает распределение нагрузки по осям для одиночного грузовика.

    Использует метод моментов сил статического равновесия относительно
    передней оси (координата 0.0). Учитывается только продольная (X) позиция
    груза - поперечное (Y) положение и высота на нагрузку по осям не влияют,
    в этой модели мы не считаем опрокидывающий момент вбок.

    Упрощения физической модели:
    - Снаряженная масса не пересчитывается через общий центр масс. Используются
      паспортные данные пустой нагрузки на каждую группу осей как константы.
    - Тандемные оси (и другие группы из 2+ осей) рассматриваются как ОДНА
      эффективная точка опоры в геометрическом центре группы. Итоговая расчётная
      нагрузка на группу делится поровну между всеми осями внутри неё.
    """
    if len(truck.axle_groups) != 2:
        raise ValueError("Для одиночного грузовика ожидается ровно 2 группы осей (передняя и задняя).")

    front_group = truck.axle_groups[0]
    rear_group = truck.axle_groups[1]

    if front_group.position != 0.0:
        raise ValueError("Координата передней оси должна быть условным нулём (0.0).")

    base_length = rear_group.position - front_group.position
    if base_length <= 0:
        raise ValueError(f"База грузовика должна быть строго больше нуля. Получено: {base_length}")

    for cargo in cargos:
        if cargo.position is None:
            raise ValueError(
                f"Груз '{cargo.name}' ещё не расставлен (position=None). "
                f"Сначала вызовите оптимизатор размещения."
            )

    total_cargo_weight = sum(cargo.weight for cargo in cargos)
    cargo_moment_around_front = sum(cargo.weight * cargo.position for cargo in cargos)

    cargo_on_rear = cargo_moment_around_front / base_length
    cargo_on_front = total_cargo_weight - cargo_on_rear

    front_total_load = front_group.empty_weight + cargo_on_front
    rear_total_load = rear_group.empty_weight + cargo_on_rear

    results = []
    critical_error_msg = None

    for group, total_load in zip([front_group, rear_group], [front_total_load, rear_total_load]):
        load_per_axle = total_load / group.axles_in_group
        is_overloaded = load_per_axle > group.max_load_per_axle
        is_lifted = total_load <= 0

        if is_lifted:
            direction = "назад" if group.name.lower().startswith("перед") else "вперёд"
            critical_error_msg = (
                f"ОПАСНО: Груз смещён слишком далеко {direction}. "
                f"{group.name} теряет сцепление с дорогой!"
            )

        results.append(AxleGroupResult(
            group=group,
            total_load=round(total_load, 1),
            load_per_axle=round(load_per_axle, 1),
            is_overloaded=is_overloaded,
            is_lifted=is_lifted
        ))

    total_weight = truck.empty_total_weight + total_cargo_weight
    is_total_overloaded = total_weight > truck.max_total_weight

    return CalculateResult(
        axle_results=results,
        total_weight=round(total_weight, 1),
        is_total_overloaded=is_total_overloaded,
        critical_error=critical_error_msg
    )