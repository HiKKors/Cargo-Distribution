import flet as ft
from core.models import Truck, AxleGroup, Cargo
from data.manual_source import ManualCargoDataSource
from core.optimizer import find_safe_placement

DEFAULT_TRUCK = Truck(
    name="КамАЗ 4308",
    max_total_weight=11900,
    body_length=6.0,
    body_start_offset=1.0,
    axle_groups=[
        AxleGroup("Передняя ось", 0.0, 3200, 4300, 1),
        AxleGroup("Задняя ось", 4.2, 2300, 7600, 1)
    ]
)

def create_truck_card(truck: Truck):
    return ft.Card(
        content=ft.Container(
            padding=15,
            content=ft.Column([
                ft.Text("Транспортное средство", size=20, weight=ft.FontWeight.BOLD),
                ft.Text(f"Модель: {truck.name}"),
                ft.Text(f"База: {truck.axle_groups[-1].position} м | Кузов: {truck.body_length} м (отступ: {truck.body_start_offset} м)"),
                ft.Text(f"Макс. масса: {truck.max_total_weight} кг"),
            ])
        )
    )

class CargoForm(ft.Card):
    def __init__(self, state, cargo_source, on_change):
        super().__init__()
        self.state = state
        self.cargo_source = cargo_source
        self.on_change = on_change

        self.name_input = ft.TextField(label="Название", expand=True)
        self.weight_input = ft.TextField(label="Вес (кг)", value="1000", width=100)
        self.length_input = ft.TextField(label="Длина (м)", value="1.0", width=100)

        self.cargo_list_container = ft.Column()
        self.build_cargo_list()

        self.content = ft.Container(
            padding=15,
            content=ft.Column([
                ft.Text("Грузы", size=20, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.FilledButton("Импорт из ATI.SU", icon=ft.Icons.CLOUD_DOWNLOAD, disabled=True, tooltip="Будет доступно позже"),
                    ft.Text("или введите вручную:", color=ft.Colors.GREY_500)
                ]),
                ft.Row([
                    self.name_input,
                    self.weight_input,
                    self.length_input,
                    ft.FilledButton("Добавить", on_click=self.add_cargo)
                ], alignment=ft.MainAxisAlignment.START),
                ft.Divider(),
                ft.FilledButton(
                    "Расставить автоматически", 
                    icon=ft.Icons.AUTO_FIX_HIGH, 
                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE), 
                    on_click=self.auto_arrange, 
                    width=float('inf')
                ),
                self.cargo_list_container
            ])
        )

    def show_snack(self, message: str, color: str):
        snack = ft.SnackBar(content=ft.Text(message), bgcolor=color)
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    def add_cargo(self, e):
        if not self.name_input.value:
            self.show_snack("Укажите название груза", ft.Colors.ORANGE)
            return
        try:
            cargo = Cargo(
                name=self.name_input.value,
                weight=float(self.weight_input.value or 0),
                length=float(self.length_input.value or 0)
            )
            self.cargo_source.add_cargo(cargo)
            self.name_input.value = ""
            self.build_cargo_list()
            if self.page:
                self.update()
            self.on_change()
        except ValueError as err:
            self.show_snack(str(err), ft.Colors.RED)

    def remove_cargo(self, idx):
        self.cargo_source.remove_cargo(idx)
        self.build_cargo_list()
        if self.page:
            self.update()
        self.on_change()

    def auto_arrange(self, e):
        cargos = self.cargo_source.get_cargos()
        if not cargos:
            self.show_snack("Нет грузов для расстановки", ft.Colors.ORANGE)
            return
        
        truck = self.state['truck']
        placed_cargos = find_safe_placement(truck, cargos)
        
        if placed_cargos is None:
            self.show_snack("Невозможно безопасно разместить эти грузы", ft.Colors.RED)
        else:
            self.cargo_source.clear()
            for c in placed_cargos:
                self.cargo_source.add_cargo(c)
            self.show_snack("Грузы успешно расставлены!", ft.Colors.GREEN)
            self.build_cargo_list()
            if self.page:
                self.update()
            self.on_change()

    def build_cargo_list(self):
        cargos = self.cargo_source.get_cargos()
        self.cargo_list_container.controls.clear()
        
        if not cargos:
            self.cargo_list_container.controls.append(ft.Text("Грузов пока нет", color=ft.Colors.GREY_500, italic=True))
        else:
            for i, c in enumerate(cargos):
                pos_text = f"на {round(c.position, 2)} м" if c.position is not None else "не расставлен"
                self.cargo_list_container.controls.append(
                    ft.Row([
                        ft.Text(f"{c.name}: {c.weight} кг, {c.length} м | {pos_text}", expand=True),
                        ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED, on_click=lambda e, idx=i: self.remove_cargo(idx))
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                )