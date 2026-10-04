import flet as ft
import flet.canvas as cvs
from typing import List, Optional
from core.models import Truck, Cargo, CalculateResult

_SCALE_MIN = 35
_SCALE_MAX = 100

# Цвета для грузов (циклически)
_CARGO_COLORS = [
    ft.Colors.AMBER_300,
    ft.Colors.LIGHT_GREEN_300,
    ft.Colors.LIGHT_BLUE_300,
    ft.Colors.ORANGE_300,
    ft.Colors.PINK_300,
    ft.Colors.PURPLE_200,
    ft.Colors.TEAL_200,
    ft.Colors.YELLOW_400,
]
_CARGO_BORDER_COLORS = [
    ft.Colors.AMBER_900,
    ft.Colors.GREEN_700,
    ft.Colors.BLUE_700,
    ft.Colors.ORANGE_900,
    ft.Colors.PINK_900,
    ft.Colors.PURPLE_700,
    ft.Colors.TEAL_700,
    ft.Colors.YELLOW_900,
]


def _compute_scale(page_width: float, truck: Truck) -> int:
    """Масштаб по X (px/м), чтобы грузовик целиком вписался в ширину экрана."""
    truck_meters = truck.body_start_offset + truck.body_length
    available_px = max(200, page_width - 120)
    scale = int(available_px / truck_meters)
    return max(_SCALE_MIN, min(_SCALE_MAX, scale))


# ── Вид СВЕРХУ (план) ────────────────────────────────────────────────────────

def _draw_top_view(
    truck: Truck,
    cargos: List[Cargo],
    calc_result: Optional[CalculateResult],
    sx: int,   # масштаб по X (длина)
) -> cvs.Canvas:
    """
    Вид сверху: длина кузова — по горизонтали, ширина — по вертикали.
    Ось X (sx px/м), ось Y — масштабируется так, чтобы ширина кузова
    занимала не менее 120 px.
    """
    # Масштаб по Y выбирается так, чтобы body_width было >= 120px
    sy = max(sx, int(120 / max(truck.body_width, 0.1)))

    margin_l = 30   # отступ слева (до передней оси)
    margin_t = 20   # отступ сверху
    margin_b = 10   # отступ снизу

    body_l_px = int(truck.body_length * sx)
    body_w_px = int(truck.body_width  * sy)
    cabin_px  = int(truck.body_start_offset * sx)

    canvas_w = margin_l + cabin_px + body_l_px + 20
    canvas_h = margin_t + body_w_px + margin_b

    shapes: list = []

    # Опорная координата передней оси в canvas = margin_l
    # Тело кузова начинается с margin_l + cabin_px
    body_x = margin_l + cabin_px
    body_y = margin_t

    # ── Кабина (заштрихованная область до кузова) ─────────────────────────
    shapes.append(cvs.Rect(
        x=margin_l, y=body_y, width=cabin_px, height=body_w_px,
        paint=ft.Paint(color=ft.Colors.BLUE_GREY_200, style=ft.PaintingStyle.FILL),
    ))
    shapes.append(cvs.Rect(
        x=margin_l, y=body_y, width=cabin_px, height=body_w_px,
        paint=ft.Paint(color=ft.Colors.BLUE_GREY_500, style=ft.PaintingStyle.STROKE, stroke_width=1),
    ))

    # ── Контур кузова ─────────────────────────────────────────────────────
    shapes.append(cvs.Rect(
        x=body_x, y=body_y, width=body_l_px, height=body_w_px,
        paint=ft.Paint(color=ft.Colors.BLUE_GREY_50, style=ft.PaintingStyle.FILL),
    ))
    shapes.append(cvs.Rect(
        x=body_x, y=body_y, width=body_l_px, height=body_w_px,
        paint=ft.Paint(color=ft.Colors.BLUE_GREY_500, style=ft.PaintingStyle.STROKE, stroke_width=2),
    ))

    # ── Линии осей (вертикальные, через всю ширину) ───────────────────────
    for i, group in enumerate(truck.axle_groups):
        ax_x = margin_l + int(group.position * sx)
        overloaded = calc_result and calc_result.axle_results[i].is_overloaded
        color = ft.Colors.RED_600 if overloaded else ft.Colors.BLUE_700
        shapes.append(cvs.Line(
            x1=ax_x, y1=body_y - 8,
            x2=ax_x, y2=body_y + body_w_px + 8,
            paint=ft.Paint(color=color, stroke_width=2),
        ))
        # Подпись нагрузки под осью
        if calc_result:
            r = calc_result.axle_results[i]
            label_color = ft.Colors.RED_600 if r.is_overloaded else ft.Colors.GREEN_700
            shapes.append(cvs.Text(
                x=ax_x - 25, y=body_y + body_w_px + 12,
                value=f"{r.total_load} кг",
                style=ft.TextStyle(color=label_color, weight=ft.FontWeight.BOLD, size=12),
            ))

    # ── Грузы ─────────────────────────────────────────────────────────────
    for idx, cargo in enumerate(cargos):
        if cargo.position is None or cargo.lateral_position is None:
            continue
        c_left = body_x + int((cargo.position - cargo.length / 2) * sx)
        c_top  = body_y + int((cargo.lateral_position - cargo.width / 2) * sy)
        c_w    = max(4, int(cargo.length * sx))
        c_h    = max(4, int(cargo.width  * sy))

        fill_color   = _CARGO_COLORS[idx % len(_CARGO_COLORS)]
        border_color = _CARGO_BORDER_COLORS[idx % len(_CARGO_BORDER_COLORS)]

        shapes.append(cvs.Rect(
            x=c_left, y=c_top, width=c_w, height=c_h,
            paint=ft.Paint(color=fill_color, style=ft.PaintingStyle.FILL),
        ))
        shapes.append(cvs.Rect(
            x=c_left, y=c_top, width=c_w, height=c_h,
            paint=ft.Paint(color=border_color, style=ft.PaintingStyle.STROKE, stroke_width=1),
        ))
        # Подпись: название + вес
        if c_w > 25 and c_h > 14:
            shapes.append(cvs.Text(
                x=c_left + 3, y=c_top + min(14, c_h // 2 + 5),
                value=f"{cargo.name}",
                style=ft.TextStyle(color=ft.Colors.BLACK, size=10, weight=ft.FontWeight.W_600),
            ))
        if c_w > 40 and c_h > 26:
            shapes.append(cvs.Text(
                x=c_left + 3, y=c_top + min(28, c_h - 4),
                value=f"{cargo.weight}кг",
                style=ft.TextStyle(color=ft.Colors.BLACK_54, size=9),
            ))

    # ── Размерные подписи ─────────────────────────────────────────────────
    # Ширина кузова — справа
    shapes.append(cvs.Text(
        x=body_x + body_l_px + 4, y=body_y + body_w_px // 2,
        value=f"{truck.body_width}м",
        style=ft.TextStyle(color=ft.Colors.GREY_600, size=10),
    ))

    canvas_h_with_labels = canvas_h + (30 if calc_result else 0)
    return cvs.Canvas(shapes=shapes, width=canvas_w, height=canvas_h_with_labels)


# ── Вид СБОКУ (нагрузки на оси) ─────────────────────────────────────────────

def _draw_side_view(
    truck: Truck,
    calc_result: Optional[CalculateResult],
    sx: int,
) -> cvs.Canvas:
    """
    Упрощённый вид сбоку: только шасси, кабина и оси с нагрузками.
    Грузы не рисуются (они показаны в виде сверху).
    """
    axle_y    = 100
    chassis_y = 70
    chassis_h = 12

    start_x = 20
    end_x   = 30 + int((truck.body_start_offset + truck.body_length) * sx) + 20

    shapes: list = []

    # Рама
    shapes.append(cvs.Rect(
        x=start_x, y=chassis_y, width=end_x - start_x, height=chassis_h,
        paint=ft.Paint(color=ft.Colors.BLUE_GREY_800),
    ))

    # Кабина
    cabin_end = 30 + int(truck.body_start_offset * sx) - 5
    shapes.append(cvs.Rect(
        x=start_x, y=30, width=cabin_end - start_x, height=40,
        paint=ft.Paint(color=ft.Colors.BLUE_GREY_300),
    ))

    # Платформа кузова
    plat_x = 30 + int(truck.body_start_offset * sx)
    shapes.append(cvs.Rect(
        x=plat_x, y=chassis_y - 4, width=int(truck.body_length * sx), height=4,
        paint=ft.Paint(color=ft.Colors.BLUE_GREY_500),
    ))

    # Оси с нагрузками
    if calc_result:
        for group, gr in zip(truck.axle_groups, calc_result.axle_results):
            ax_x = 30 + int(group.position * sx)
            text_color = ft.Colors.RED if (gr.is_overloaded or gr.is_lifted) else ft.Colors.GREEN
            shapes.append(cvs.Circle(x=ax_x, y=axle_y, radius=18,
                                     paint=ft.Paint(color=ft.Colors.BLUE_GREY_900)))
            shapes.append(cvs.Circle(x=ax_x, y=axle_y, radius=8,
                                     paint=ft.Paint(color=ft.Colors.GREY_400)))
            shapes.append(cvs.Text(
                x=ax_x - 28, y=axle_y + 28,
                value=f"{gr.total_load} кг",
                style=ft.TextStyle(color=text_color, weight=ft.FontWeight.BOLD, size=13),
            ))
            shapes.append(cvs.Text(
                x=ax_x - 32, y=axle_y + 44,
                value=f"Макс: {group.max_load_per_axle * group.axles_in_group} кг",
                style=ft.TextStyle(color=ft.Colors.GREY_500, size=10),
            ))

    canvas_w = end_x + 20
    return cvs.Canvas(shapes=shapes, width=canvas_w, height=160)


# ── Точка входа ──────────────────────────────────────────────────────────────

def update_visualization(
    container: ft.Container,
    truck: Truck,
    cargos: List[Cargo],
    calc_result: Optional[CalculateResult],
    page_width: float = 400,
):
    unplaced = any(c.position is None or c.lateral_position is None for c in cargos)
    if unplaced:
        container.content = ft.Text(
            'Нажмите «Расставить автоматически», чтобы найти безопасные позиции',
            color=ft.Colors.GREY_500, italic=True,
        )
        return

    if not calc_result and not cargos:
        container.content = ft.Text(
            'Добавьте груз для расчёта', color=ft.Colors.GREY_500, italic=True,
        )
        return

    sx = _compute_scale(page_width, truck)

    top_canvas  = _draw_top_view(truck, cargos, calc_result, sx)
    side_canvas = _draw_side_view(truck, calc_result, sx)

    col = ft.Column([
        # ── Вид сверху ──────────────────────────────────────────────────
        ft.Text("Вид сверху — план кузова", weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
        ft.Row([top_canvas], scroll=ft.ScrollMode.AUTO),
        ft.Divider(height=8),
        # ── Вид сбоку ───────────────────────────────────────────────────
        ft.Text("Нагрузки по осям", weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
        ft.Row([side_canvas], scroll=ft.ScrollMode.AUTO),
    ], spacing=6)

    # ── Критическая ошибка ──────────────────────────────────────────────
    if calc_result and calc_result.critical_error:
        col.controls.insert(0, ft.Container(
            content=ft.Text(
                calc_result.critical_error,
                weight=ft.FontWeight.BOLD, color=ft.Colors.RED_600, size=16,
            ),
            bgcolor=ft.Colors.RED_100, padding=10, border_radius=8,
        ))

    # ── Итоговая масса ──────────────────────────────────────────────────
    if calc_result:
        total_color = (
            ft.Colors.RED_600 if calc_result.is_total_overloaded
            else ft.Colors.GREEN_600
        )
        col.controls.append(ft.Text(
            f"Полная масса: {calc_result.total_weight} кг  "
            f"(разрешено: {truck.max_total_weight} кг)",
            color=total_color, weight=ft.FontWeight.BOLD, size=16,
        ))

    container.content = col