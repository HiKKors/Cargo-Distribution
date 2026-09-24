import flet as ft
import copy
from core.physics import calculate_loads
from data.manual_source import ManualCargoDataSource
from ui.components import DEFAULT_TRUCK, create_truck_card, CargoForm
from ui.visualizer import update_visualization

def main(page: ft.Page):
    page.title = "Axle Load MVP"
    page.scroll = ft.ScrollMode.AUTO
    page.theme_mode = ft.ThemeMode.LIGHT
    
    page.appbar = ft.AppBar(
        title=ft.Text("Расчет нагрузки по осям", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
        bgcolor=ft.Colors.BLUE_800,
    )

    state = {'truck': copy.deepcopy(DEFAULT_TRUCK)}
    cargo_source = ManualCargoDataSource()

    visualizer_container = ft.Container(margin=ft.Margin(top=20, left=0, right=0, bottom=0))

    def on_state_change():
        cargos = cargo_source.get_cargos()
        unplaced = any(c.position is None for c in cargos)
        
        if unplaced and len(cargos) > 0:
            result = None
        else:
            try:
                result = calculate_loads(state['truck'], cargos)
            except Exception as e:
                snack = ft.SnackBar(content=ft.Text(f'Ошибка расчета: {str(e)}'), bgcolor=ft.Colors.RED)
                page.overlay.append(snack)
                snack.open = True
                page.update()
                result = None

        update_visualization(visualizer_container, state['truck'], cargos, result)
        page.update()

    truck_card = create_truck_card(state['truck'])
    cargo_form = CargoForm(state, cargo_source, on_state_change)

    page.add(
        ft.ResponsiveRow([
            ft.Column([truck_card], col={"sm": 12, "md": 6}),
            ft.Column([cargo_form], col={"sm": 12, "md": 6})
        ]),
        ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    ft.Text("Схема распределения", size=20, weight=ft.FontWeight.BOLD),
                    visualizer_container
                ])
            )
        )
    )
    
    # Первичный рендер заглушки
    on_state_change()