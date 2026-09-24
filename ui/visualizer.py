import flet as ft
import flet.canvas as cvs
from typing import List, Optional
from core.models import Truck, Cargo, CalculateResult

def update_visualization(container: ft.Container, truck: Truck, cargos: List[Cargo], calc_result: Optional[CalculateResult]):
    unplaced = any(c.position is None for c in cargos)
    if unplaced:
        container.content = ft.Text('Нажмите "Расставить автоматически", чтобы найти безопасные позиции', color=ft.Colors.GREY_500, italic=True)
        return

    if not calc_result and not cargos:
        container.content = ft.Text('Добавьте груз для расчета', color=ft.Colors.GREY_500, italic=True)
        return

    SCALE = 100
    canvas_width = max(800, (truck.body_start_offset + truck.body_length) * SCALE + 200)
    shapes = []

    # Базовые координаты по вертикали
    axle_y = 180
    chassis_y = 150
    chassis_height = 15
    
    # 1. Основная рама (шасси) грузовика (идет от носа до конца кузова)
    start_x = 20
    end_x = 50 + (truck.body_start_offset + truck.body_length) * SCALE
    shapes.append(cvs.Rect(x=start_x, y=chassis_y, width=end_x - start_x, height=chassis_height, paint=ft.Paint(color=ft.Colors.BLUE_GREY_800)))

    # 2. Кабина (условный блок над передней осью)
    cabin_end_x = 50 + truck.body_start_offset * SCALE - 10
    shapes.append(cvs.Rect(x=start_x, y=70, width=cabin_end_x - start_x, height=80, paint=ft.Paint(color=ft.Colors.BLUE_GREY_300)))

    # 3. Грузовая платформа
    platform_start_x = 50 + truck.body_start_offset * SCALE
    shapes.append(cvs.Rect(x=platform_start_x, y=chassis_y - 5, width=truck.body_length * SCALE, height=5, paint=ft.Paint(color=ft.Colors.BLUE_GREY_500)))

    # 4. Оси и расчетные подписи
    if calc_result:
        for group, group_res in zip(truck.axle_groups, calc_result.axle_results):
            x_pos = 50 + group.position * SCALE
            
            # Внешний контур колеса
            shapes.append(cvs.Circle(x=x_pos, y=axle_y, radius=22, paint=ft.Paint(color=ft.Colors.BLUE_GREY_900)))
            # Внутренний диск
            shapes.append(cvs.Circle(x=x_pos, y=axle_y, radius=10, paint=ft.Paint(color=ft.Colors.GREY_400)))
            
            text_color = ft.Colors.RED if (group_res.is_overloaded or group_res.is_lifted) else ft.Colors.GREEN
            shapes.append(cvs.Text(x=x_pos - 25, y=axle_y + 35, value=f"{group_res.total_load} кг", style=ft.TextStyle(color=text_color, weight=ft.FontWeight.BOLD, size=16)))
            shapes.append(cvs.Text(x=x_pos - 35, y=axle_y + 55, value=f"Макс: {group.max_load_per_axle * group.axles_in_group} кг", style=ft.TextStyle(color=ft.Colors.GREY_500, size=12)))

    # 5. Отрисовка грузов
    cargo_y = chassis_y - 5 - 60  # платформа минус высота груза
    for cargo in cargos:
        if cargo.position is not None:
            width_px = cargo.length * SCALE
            x_start = 50 + (cargo.position * SCALE) - (width_px / 2)
            
            # Фон груза
            shapes.append(cvs.Rect(x=x_start, y=cargo_y, width=width_px, height=60, paint=ft.Paint(color=ft.Colors.AMBER_300, style=ft.PaintingStyle.FILL)))
            # Обводка груза
            shapes.append(cvs.Rect(x=x_start, y=cargo_y, width=width_px, height=60, paint=ft.Paint(color=ft.Colors.AMBER_900, style=ft.PaintingStyle.STROKE, stroke_width=2)))
            # Текст на грузе
            shapes.append(cvs.Text(x=x_start + (width_px / 2) - 20, y=cargo_y + 25, value=f"{cargo.weight}kg", style=ft.TextStyle(color=ft.Colors.BLACK, size=12)))

    drawing = cvs.Canvas(shapes=shapes, width=canvas_width, height=320)
    col = ft.Column([ft.Row([drawing], scroll=ft.ScrollMode.AUTO)])

    # Вывод ошибок и общей массы
    if calc_result:
        if calc_result.critical_error:
            col.controls.insert(0, ft.Container(
                content=ft.Text(calc_result.critical_error, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_600, size=20),
                bgcolor=ft.Colors.RED_100, padding=10, border_radius=8
            ))
        
        total_color = ft.Colors.RED_600 if calc_result.is_total_overloaded else ft.Colors.GREEN_600
        col.controls.append(
            ft.Text(f'Полная масса: {calc_result.total_weight} кг (Разрешено: {truck.max_total_weight} кг)', color=total_color, weight=ft.FontWeight.BOLD, size=18)
        )

    container.content = col