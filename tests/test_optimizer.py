import unittest
from core.models import Truck, AxleGroup, Cargo
from core.optimizer import find_safe_placement
from core.physics import calculate_loads


def make_kamaz(body_width=2.4):
    return Truck(
        name="КамАЗ 4308",
        max_total_weight=11900,
        body_length=6.0,
        body_width=body_width,
        body_height=2.0,
        body_start_offset=1.0,
        axle_groups=[
            AxleGroup("Передняя", 0.0, 3200, 4300, 1),
            AxleGroup("Задняя", 4.2, 2300, 7600, 1)
        ]
    )


class TestOptimizerBasic1D(unittest.TestCase):
    """Проверка на случае, где по сути всё сводится к прежней 1D-логике
    (грузы шире половины кузова, поэтому каждый занимает свою полку)."""

    def test_two_wide_cargos_sequential(self):
        truck = make_kamaz(body_width=2.4)
        cargos = [
            Cargo("Груз А", weight=2000, length=1.5, width=2.4, height=1.0),
            Cargo("Груз Б", weight=3000, length=2.0, width=2.4, height=1.0),
        ]
        placed = find_safe_placement(truck, cargos, step=0.1)
        self.assertIsNotNone(placed, "Алгоритм не нашёл расстановку, хотя она существует")

        cargo_a = next(c for c in placed if c.name == "Груз А")
        cargo_b = next(c for c in placed if c.name == "Груз Б")

        # Оба груза занимают всю ширину -> каждый на своей полке, ровно как в старой 1D-модели.
        self.assertAlmostEqual(cargo_a.position, 2.65, places=2)
        self.assertAlmostEqual(cargo_b.position, 4.4, places=2)
        self.assertAlmostEqual(cargo_a.lateral_position, 1.2, places=2)
        self.assertAlmostEqual(cargo_b.lateral_position, 1.2, places=2)

        calc_result = calculate_loads(truck, placed)
        self.assertAlmostEqual(calc_result.axle_results[0].total_load, 3795.2, delta=5)
        self.assertAlmostEqual(calc_result.axle_results[1].total_load, 6704.8, delta=5)


class TestOptimizerShelfPacking(unittest.TestCase):
    """Проверка настоящей 2D-упаковки: два узких груза встают БОК О БОК на одну полку."""

    def test_two_narrow_cargos_share_shelf(self):
        truck = make_kamaz(body_width=2.4)
        cargos = [
            Cargo("Паллета 1", weight=1000, length=1.2, width=1.0, height=1.0),
            Cargo("Паллета 2", weight=1000, length=1.2, width=1.0, height=1.0),
        ]
        placed = find_safe_placement(truck, cargos, step=0.1)
        self.assertIsNotNone(placed)

        # Обе паллеты должны встать на одну и ту же полку (одинаковый X),
        # но с разными Y (бок о бок), раз 1.0 + 1.0 = 2.0 <= 2.4 (ширина кузова).
        positions_x = {round(c.position, 2) for c in placed}
        self.assertEqual(len(positions_x), 1, "Ожидали, что обе паллеты встанут на одну полку (общий X)")

        lateral_positions = sorted(c.lateral_position for c in placed)
        self.assertAlmostEqual(lateral_positions[0], 0.5, places=2)   # первая: центр на 0.5 (0..1.0)
        self.assertAlmostEqual(lateral_positions[1], 1.5, places=2)   # вторая: центр на 1.5 (1.0..2.0)

        # Груз не должен пересекаться сам с собой по ширине
        self.assertNotAlmostEqual(lateral_positions[0], lateral_positions[1], places=2)

    def test_cargo_wider_than_body_returns_none(self):
        truck = make_kamaz(body_width=2.4)
        cargos = [Cargo("Слишком широкий", weight=1000, length=1.0, width=3.0, height=1.0)]
        placed = find_safe_placement(truck, cargos)
        self.assertIsNone(placed)

    def test_cargo_taller_than_body_returns_none(self):
        truck = make_kamaz()
        cargos = [Cargo("Слишком высокий", weight=1000, length=1.0, width=1.0, height=5.0)]
        placed = find_safe_placement(truck, cargos)
        self.assertIsNone(placed)

    def test_no_overlap_within_shelf(self):
        """Регрессионный тест: грузы на одной полке не должны перекрываться по Y."""
        truck = make_kamaz(body_width=2.4)
        cargos = [
            Cargo("A", weight=500, length=1.0, width=0.8, height=1.0),
            Cargo("B", weight=500, length=1.0, width=0.8, height=1.0),
            Cargo("C", weight=500, length=1.0, width=0.8, height=1.0),
        ]
        placed = find_safe_placement(truck, cargos, step=0.2)
        self.assertIsNotNone(placed)

        # Группируем по X (полкам) и проверяем непересечение интервалов [y_min, y_max] внутри каждой полки
        by_shelf = {}
        for c in placed:
            by_shelf.setdefault(round(c.position, 2), []).append(c)

        for shelf_cargos in by_shelf.values():
            intervals = sorted(
                (c.lateral_position - c.width / 2, c.lateral_position + c.width / 2)
                for c in shelf_cargos
            )
            for i in range(len(intervals) - 1):
                self.assertLessEqual(
                    intervals[i][1], intervals[i + 1][0] + 1e-6,
                    "Найдено пересечение грузов по ширине на одной полке"
                )

    def test_empty_cargo_list(self):
        truck = make_kamaz()
        self.assertEqual(find_safe_placement(truck, []), [])

    def test_total_length_does_not_fit(self):
        truck = make_kamaz(body_width=2.4)
        # 5 грузов по 2 метра каждый, каждый шире половины кузова -> все на отдельных полках,
        # суммарная длина блока 10 м > 6 м кузова -> размещения не существует.
        cargos = [
            Cargo(f"Груз {i}", weight=1000, length=2.0, width=2.4, height=1.0)
            for i in range(5)
        ]
        placed = find_safe_placement(truck, cargos, step=0.5)
        self.assertIsNone(placed)


if __name__ == '__main__':
    unittest.main()