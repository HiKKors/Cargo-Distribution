import itertools
import copy
from typing import List, Optional, Iterable
from .models import Truck, Cargo
from .physics import calculate_loads

# При N <= MAX_EXACT_N перебираем все N! перестановок.
# При N > MAX_EXACT_N используем эвристические порядки.
MAX_EXACT_N = 6


# ── Стратегии перебора порядков ──────────────────────────────────────────────

def _heuristic_orderings(cargos: List[Cargo]) -> List[tuple]:
    """Набор «умных» порядков: по весу, объёму, длине, бутерброд."""
    by_weight_desc = sorted(cargos, key=lambda c: c.weight, reverse=True)
    by_weight_asc  = sorted(cargos, key=lambda c: c.weight)
    by_len_desc    = sorted(cargos, key=lambda c: c.length, reverse=True)
    by_vol_desc    = sorted(cargos, key=lambda c: c.length * c.width, reverse=True)

    n = len(by_weight_desc)
    half = n // 2
    sandwich = by_weight_asc[:half] + by_weight_desc[:n - half] + list(reversed(by_weight_asc[half:]))

    candidates = [
        tuple(cargos),
        tuple(reversed(cargos)),
        tuple(by_weight_desc),
        tuple(by_weight_asc),
        tuple(by_len_desc),
        tuple(by_vol_desc),
        tuple(sandwich),
    ]
    seen: set = set()
    unique = []
    for order in candidates:
        key = tuple(id(c) for c in order)
        if key not in seen:
            seen.add(key)
            unique.append(order)
    return unique


def _iter_orderings(cargos: List[Cargo]) -> Iterable[tuple]:
    if len(cargos) <= MAX_EXACT_N:
        return itertools.permutations(cargos)
    return _heuristic_orderings(cargos)


# ── 2D-упаковка: «полочный» алгоритм ────────────────────────────────────────

def _pack_into_shelves(perm: tuple, body_width: float) -> List[List[Cargo]]:
    """
    Жадная упаковка грузов в «полки» (columns) вдоль ширины кузова.

    Грузы перебираются в порядке perm. Если очередной груз помещается
    по ширине на текущую открытую полку — добавляем туда, иначе открываем
    новую полку. Полки расположены последовательно вдоль длины кузова.
    """
    shelves: List[List[Cargo]] = []
    shelf_used_widths: List[float] = []

    for cargo in perm:     # perm - permutation (перестановка)
        placed = False
        for i in range(len(shelves)):
            if shelf_used_widths[i] + cargo.width <= body_width + 1e-9:
                shelves[i].append(cargo)
                shelf_used_widths[i] += cargo.width
                placed = True
                break
        if not placed:
            shelves.append([cargo])
            shelf_used_widths.append(cargo.width)

    return shelves


def _assign_positions(
    shelves: List[List[Cargo]],
    x_start: float,
    body_width: float = 0.0,
) -> List[Cargo]:
    """
    Назначает физические координаты центров для каждого груза.

    position (X) — центр полки по длине кузова.
    lateral_position (Y) — центр груза по ширине кузова.

    Полки идут вдоль X. Внутри каждой полки группа грузов
    центрируется по ширине кузова — груз не прижимается к стенке.
    """
    result = []
    current_x = x_start

    for shelf in shelves:
        shelf_length = max(c.length for c in shelf)
        x_center = current_x + shelf_length / 2.0

        # Центрируем группу грузов по ширине кузова
        total_w = sum(c.width for c in shelf)
        current_y = (body_width - total_w) / 2.0 if body_width > total_w else 0.0

        for cargo in shelf:
            c = copy.deepcopy(cargo)
            c.position = x_center
            c.lateral_position = current_y + cargo.width / 2.0
            result.append(c)
            current_y += cargo.width

        current_x += shelf_length

    return result


# ── Основная функция оптимизации ─────────────────────────────────────────────

def find_safe_placement(
    truck: Truck,
    cargos: List[Cargo],
    step: float = 0.1,
    strategy: str = 'balance'
) -> Optional[List[Cargo]]:
    """
    Ищет безопасное 2D-размещение грузов в кузове.

    Алгоритм:
    1. Проверяет, что каждый груз физически помещается в кузов (ширина, высота).
    2. Для каждого порядка перебора (пермутации или эвристики) упаковывает
       грузы в «полки» по ширине (2D bin packing, greedy first-fit).
    3. Скользит блок полок вдоль длины кузова с заданным шагом.
    4. На каждом шаге проверяет нагрузки через модуль physics.
    5. Из всех безопасных вариантов выбирает с наилучшим score:
       - минимальная разница % загрузки осей;
       - штраф за вынос ЦМ груза за пределы колёсной базы.
    """
    if not cargos:
        return []
    
    if strategy == 'lifo':
        return _lifo_placement(truck, cargos, step)

    # Проверка: каждый груз должен физически вписываться в кузов
    for c in cargos:
        if c.width > truck.body_width:
            return None   # груз шире кузова
        if c.height > truck.body_height:
            return None   # груз выше кузова

    best_cargos: Optional[List[Cargo]] = None
    best_score = float('inf')

    front_ax  = truck.axle_groups[0].position
    rear_ax   = truck.axle_groups[-1].position
    wheelbase = rear_ax - front_ax

    for perm in _iter_orderings(cargos):
        shelves = _pack_into_shelves(perm, truck.body_width)

        # Суммарная длина блока полок по X
        total_x = sum(max(c.length for c in shelf) for shelf in shelves)
        if total_x > truck.body_length:
            continue  # не влезает в кузов

        max_x_start = truck.body_start_offset + truck.body_length - total_x
        x_start = truck.body_start_offset

        while x_start <= max_x_start + 0.001:
            test_cargos = _assign_positions(shelves, x_start, truck.body_width)
            calc_result = calculate_loads(truck, test_cargos)

            is_safe = True
            if calc_result.critical_error or calc_result.is_total_overloaded:
                is_safe = False
            else:
                for ax in calc_result.axle_results:
                    if ax.is_overloaded or ax.is_lifted:
                        is_safe = False
                        break

            if is_safe:
                front = calc_result.axle_results[0]
                rear  = calc_result.axle_results[1]

                front_pct = front.total_load / (front.group.max_load_per_axle * front.group.axles_in_group)
                rear_pct  = rear.total_load  / (rear.group.max_load_per_axle  * rear.group.axles_in_group)

                # Критерий 1: баланс % загрузки осей
                balance = abs(front_pct - rear_pct)

                # Критерий 2: штраф за вынос ЦМ груза за пределы колёсной базы
                total_w  = sum(c.weight for c in test_cargos)
                cargo_cg = sum(c.position * c.weight for c in test_cargos) / total_w
                overhang = (max(0.0, cargo_cg - rear_ax) +
                            max(0.0, front_ax - cargo_cg))
                center_penalty = overhang / wheelbase

                score = balance + 0.5 * center_penalty

                if score < best_score:
                    best_score  = score
                    best_cargos = test_cargos

            x_start += step

    return best_cargos

def _lifo_placement(truck: Truck, cargos: List[Cargo], step: float=0.1):
    
    if not cargos:
        return []
    
    
    for c in cargos:
        if c.width > truck.body_width:
            return None
        if c.height > truck.body_height:
            return None
        
    shelves = _pack_into_shelves(tuple(cargos), truck.body_width)
    
    #суммарная длина полок по X
    total_length = sum(max(c.length for c in shelf) for shelf in shelves)
    
    if total_length > truck.body_length:
        return None
    
    # начальная позиция - передняя стенка кузова
    x_start = truck.body_start_offset
    max_x_start = truck.body_start_offset + truck.body_length - total_length
    
    while x_start < max_x_start + 0.001:
        # получаем координаты грузов
        test_cargos = _assign_positions(shelves, x_start, truck.body_width)
        calc_result = calculate_loads(truck, test_cargos)
        
        is_safe = True
        if calc_result.critical_error or calc_result.is_total_overloaded:
            is_safe = False
        else:
            for ax in calc_result.axle_results:
                if ax.is_overloaded or ax.is_lifted:
                    is_safe = False
                    break
                
        if is_safe:
            return test_cargos
        else:
            x_start += step
        
    return None
        
        