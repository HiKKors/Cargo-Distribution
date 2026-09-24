import itertools
import copy
from typing import List, Optional
from .models import Truck, Cargo
from .physics import calculate_loads

def find_safe_placement(truck: Truck, cargos: List[Cargo], step: float = 0.1) -> Optional[List[Cargo]]:
    if not cargos:
        return []

    total_length = sum(c.length for c in cargos)
    if total_length > truck.body_length:
        return None  # Груз физически не влезает в кузов

    best_cargos = None
    best_score = float('inf')

    # Перебираем все возможные порядки расстановки грузов
    for perm in itertools.permutations(cargos):
        # Крайняя позиция блока, чтобы не выпасть из кузова
        max_x = truck.body_start_offset + truck.body_length - total_length
        x_start = truck.body_start_offset
        
        while x_start <= max_x + 0.001:
            test_cargos = []
            current_offset = x_start
            
            for c in perm:
                cargo_copy = copy.deepcopy(c)
                # Вычисляем координату центра груза для физики
                cargo_copy.position = current_offset + (c.length / 2.0)
                test_cargos.append(cargo_copy)
                current_offset += c.length

            # Проверяем через физику
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
                # Оцениваем баланс загрузки
                front = calc_result.axle_results[0]
                rear = calc_result.axle_results[1]
                
                front_pct = front.total_load / (front.group.max_load_per_axle * front.group.axles_in_group)
                rear_pct = rear.total_load / (rear.group.max_load_per_axle * rear.group.axles_in_group)
                
                score = abs(front_pct - rear_pct)
                
                if score < best_score:
                    best_score = score
                    best_cargos = test_cargos

            x_start += step

    return best_cargos