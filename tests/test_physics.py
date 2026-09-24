import unittest
from core.models import Truck, AxleGroup, Cargo
from core.physics import calculate_loads


def make_kamaz():
    return Truck(
        name="КамАЗ 4308",
        max_total_weight=11900,
        body_length=6.0,
        body_width=2.4,
        body_height=2.0,
        body_start_offset=1.0,
        axle_groups=[
            AxleGroup("Передняя ось", 0.0, 3200, 4300, 1),
            AxleGroup("Задняя ось", 4.2, 2300, 7600, 1)
        ]
    )


class TestPhysicsCalculation(unittest.TestCase):

    def setUp(self):
        self.truck_2_axle = make_kamaz()

    def test_2_axle_normal_load(self):
        cargos = [Cargo(name="Станок", weight=2000, length=1.0, width=1.0, height=1.0, position=3.0)]
        result = calculate_loads(self.truck_2_axle, cargos)
        self.assertIsNone(result.critical_error)
        self.assertEqual(result.axle_results[0].total_load, 3771.4)
        self.assertEqual(result.axle_results[1].total_load, 3728.6)
        self.assertFalse(result.axle_results[0].is_overloaded)

    def test_critical_lift_error(self):
        cargos = [Cargo(name="Плита", weight=15000, length=1.0, width=1.0, height=1.0, position=6.0)]
        result = calculate_loads(self.truck_2_axle, cargos)
        self.assertTrue(result.axle_results[0].is_lifted)
        self.assertIsNotNone(result.critical_error)
        self.assertIn("ОПАСНО", result.critical_error)

    def test_base_length_must_be_positive(self):
        bad_truck = make_kamaz()
        bad_truck.axle_groups[1].position = 0.0  # совпадает с передней осью
        with self.assertRaises(ValueError):
            calculate_loads(bad_truck, [])

    def test_axles_in_group_validation(self):
        with self.assertRaises(ValueError):
            AxleGroup("Тандем", 4.2, 5000, 8000, axles_in_group=0)

    def test_unplaced_cargo_raises(self):
        cargos = [Cargo(name="Без позиции", weight=1000, length=1.0, width=1.0, height=1.0)]
        with self.assertRaises(ValueError):
            calculate_loads(self.truck_2_axle, cargos)

    def test_cargo_validation(self):
        with self.assertRaises(ValueError):
            Cargo(name="Плохой вес", weight=0, length=1.0, width=1.0, height=1.0)
        with self.assertRaises(ValueError):
            Cargo(name="Плохая длина", weight=100, length=-1.0, width=1.0, height=1.0)
        with self.assertRaises(ValueError):
            Cargo(name="Плохая ширина", weight=100, length=1.0, width=0, height=1.0)
        with self.assertRaises(ValueError):
            Cargo(name="Плохая высота", weight=100, length=1.0, width=1.0, height=0)


if __name__ == '__main__':
    unittest.main()