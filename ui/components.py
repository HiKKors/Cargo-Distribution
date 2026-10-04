import flet as ft
from core.models import Truck, AxleGroup, Cargo
from data.manual_source import ManualCargoDataSource
from core.optimizer import find_safe_placement

DEFAULT_TRUCK = Truck(
    name="КамАЗ 4308",
    max_total_weight=11900,
    body_length=6.0,
    body_width=2.4,
    body_height=2.0,
    body_start_offset=1.0,
    axle_groups=[
        AxleGroup("Передняя ось", 0.0, 3200, 4300, 1),
        AxleGroup("Задняя ось",   4.2, 2300, 7600, 1),
    ]
)


def create_truck_card(truck: Truck):
    return ft.Card(
        content=ft.Container(
            padding=15,
            content=ft.Column([
                ft.Text("Транспортное средство", size=20, weight=ft.FontWeight.BOLD),
                ft.Text(f"Модель: {truck.name}"),
                ft.Text(
                    f"База: {truck.axle_groups[-1].position} м  |  "
                    f"Кузов (Д×Ш×В): {truck.body_length} × {truck.body_width} × {truck.body_height} м"
                ),
                ft.Text(
                    f"Отступ кузова: {truck.body_start_offset} м  |  "
                    f"Макс. масса: {truck.max_total_weight} кг"
                ),
            ])
        )
    )


class CargoForm(ft.Card):
    def __init__(self, state, cargo_source: ManualCargoDataSource, on_change):
        super().__init__()
        self.state        = state
        self.cargo_source = cargo_source
        self.on_change    = on_change

        self.name_input = ft.TextField(
            label="Название груза",
            expand=True,
            keyboard_type=ft.KeyboardType.TEXT,
        )

        # ── Размеры и вес ────────────────────────────────────────────────────
        field_w = 90
        self.weight_input = ft.TextField(
            label="Вес, кг", value="500", width=field_w,
            keyboard_type=ft.KeyboardType.NUMBER,
            input_filter=ft.NumbersOnlyInputFilter(),
        )
        self.length_input = ft.TextField(
            label="Длина, м", value="1.2", width=field_w,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self.width_input = ft.TextField(
            label="Ширина, м", value="1.0", width=field_w,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self.height_input = ft.TextField(
            label="Высота, м", value="1.0", width=field_w,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        self.cargo_list_container = ft.Column(spacing=4)
        self.build_cargo_list()

        self.content = ft.Container(
            padding=15,
            content=ft.Column([
                ft.Text("Грузы", size=20, weight=ft.FontWeight.BOLD),

                # ── Строка 1: название + добавить ─────────────────────────
                ft.Row([
                    self.name_input,
                    ft.FilledButton("Добавить", icon=ft.Icons.ADD, on_click=self.add_cargo),
                ], alignment=ft.MainAxisAlignment.START),

                # ── Строка 2: вес + длина ─────────────────────────────────
                ft.Row([self.weight_input, self.length_input], spacing=8),

                # ── Строка 3: ширина + высота ─────────────────────────────
                ft.Row([self.width_input, self.height_input], spacing=8),

                ft.Divider(height=8),

                # ── Кнопка авторасстановки ────────────────────────────────
                ft.FilledButton(
                    "Расставить автоматически",
                    icon=ft.Icons.AUTO_FIX_HIGH,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.GREEN,
                        color=ft.Colors.WHITE,
                        padding=ft.Padding(left=16, top=16, right=16, bottom=16),
                    ),
                    on_click=self.auto_arrange,
                    width=float('inf'),
                ),
                ft.Divider(height=4),
                ft.FilledButton(
                    "Импорт из ATI.SU",
                    icon=ft.Icons.CLOUD_DOWNLOAD,
                    disabled=True,
                    tooltip="Будет доступно позже",
                    width=float('inf'),
                ),
                self.cargo_list_container,
            ], spacing=10)
        )

    # ── Helpers ──────────────────────────────────────────────────────────────

    def show_snack(self, message: str, color: str):
        snack = ft.SnackBar(content=ft.Text(message), bgcolor=color)
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    # ── Обработчики ──────────────────────────────────────────────────────────

    def add_cargo(self, e):
        if not self.name_input.value:
            self.show_snack("Укажите название груза", ft.Colors.ORANGE)
            return
        try:
            cargo = Cargo(
                name=self.name_input.value,
                weight=float(self.weight_input.value or 0),
                length=float(self.length_input.value or 0),
                width=float(self.width_input.value or 0),
                height=float(self.height_input.value or 0),
            )
            self.cargo_source.add_cargo(cargo)
            self.name_input.value = ""
            self.build_cargo_list()
            if self.page:
                self.update()
            self.on_change()
        except ValueError as err:
            self.show_snack(str(err), ft.Colors.RED)

    def remove_cargo(self, idx: int):
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
            self.cargo_source.replace_all(placed_cargos)
            self.show_snack("Грузы успешно расставлены!", ft.Colors.GREEN)
            self.build_cargo_list()
            if self.page:
                self.update()
            self.on_change()

    # ── Список грузов ────────────────────────────────────────────────────────

    def build_cargo_list(self):
        cargos = self.cargo_source.get_cargos()
        self.cargo_list_container.controls.clear()

        if not cargos:
            self.cargo_list_container.controls.append(
                ft.Text("Грузов пока нет", color=ft.Colors.GREY_500, italic=True)
            )
            return

        for i, c in enumerate(cargos):
            if c.position is not None and c.lateral_position is not None:
                pos_text = (
                    f"X={round(c.position, 2)} м  Y={round(c.lateral_position, 2)} м"
                )
            else:
                pos_text = "не расставлен"

            self.cargo_list_container.controls.append(
                ft.Container(
                    padding=ft.Padding(left=4, top=6, right=4, bottom=6),
                    content=ft.Row([
                        ft.Column([
                            ft.Text(c.name, weight=ft.FontWeight.W_600),
                            ft.Text(
                                f"{c.weight} кг  |  {c.length}×{c.width}×{c.height} м  |  {pos_text}",
                                size=12, color=ft.Colors.GREY_600,
                            ),
                        ], expand=True, spacing=2),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=ft.Colors.RED_400,
                            icon_size=28,
                            style=ft.ButtonStyle(
                                padding=ft.Padding(left=12, top=12, right=12, bottom=12),
                            ),
                            tooltip="Удалить груз",
                            on_click=lambda e, idx=i: self.remove_cargo(idx),
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
                )
            )