"""Behavioral regression tests for the car rental demo."""

import os
import stat
import unittest
from pathlib import Path
from unittest.mock import patch

import car_rental


class CarRentalTests(unittest.TestCase):
    """Verify core booking, customer, security, and receipt behavior."""

    def setUp(self) -> None:
        car_rental.connection.execute("DELETE FROM customers")
        car_rental.fleet.clear()
        car_rental.bookings.clear()
        car_rental.register_customer("O'Neil", "DL-0420110012345", "5550100")

    def test_customer_lookup_and_hashed_licence(self) -> None:
        self.assertEqual(
            car_rental.find_customer("O'Neil"),
            [("O'Neil", "5550100")],
        )
        self.assertEqual(car_rental.find_customer("x' OR '1'='1"), [])
        stored_hash = car_rental.connection.execute(
            "SELECT licence_hash FROM customers"
        ).fetchone()[0]
        self.assertNotEqual(
            stored_hash,
            "DL-0420110012345",
        )
        self.assertTrue(
            car_rental.verify_licence("DL-0420110012345", stored_hash)
        )
        self.assertFalse(car_rental.verify_licence("incorrect", stored_hash))

    def test_booking_availability_and_date_validation(self) -> None:
        car_rental.add_car("KA01AB1234", "Swift", 1500)
        car_rental.add_car("KA02CD5678", "Innova", 3000)
        self.assertEqual(
            car_rental.rent_car(
                "KA01AB1234", "O'Neil", "2026-11-01", "2026-11-04"
            ),
            4500,
        )
        self.assertNotIn("KA01AB1234", car_rental.available_cars())
        with self.assertRaisesRegex(ValueError, "not available"):
            car_rental.rent_car(
                "KA01AB1234", "O'Neil", "2026-11-02", "2026-11-03"
            )
        with self.assertRaisesRegex(ValueError, "cannot precede"):
            car_rental.rent_car(
                "KA02CD5678", "O'Neil", "2026-11-10", "2026-11-07"
            )
        self.assertIn("KA02CD5678", car_rental.available_cars())

    def test_return_and_extra_kilometre_charge(self) -> None:
        car_rental.add_car("KA01AB1234", "Swift", 1500)
        car_rental.add_car("KA02CD5678", "Innova", 3000)
        car_rental.rent_car(
            "KA01AB1234", "O'Neil", "2026-11-01", "2026-11-04"
        )
        self.assertEqual(car_rental.return_car("KA01AB1234", 420), 600)
        self.assertIn("KA01AB1234", car_rental.available_cars())
        car_rental.rent_car(
            "KA02CD5678", "O'Neil", "2026-11-01", "2026-11-04"
        )
        self.assertEqual(car_rental.return_car("KA02CD5678", 300), 0)
        with self.assertRaisesRegex(ValueError, "no active rental"):
            car_rental.return_car("KA02CD5678", 300)
        with self.assertRaisesRegex(ValueError, "not found"):
            car_rental.return_car("XX00XX0000", 10)

    def test_promotions_plate_and_admin_authentication(self) -> None:
        self.assertEqual(
            car_rental.apply_promo("amount = amount * 0.9", 4500),
            4050,
        )
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            car_rental.apply_promo("__import__('os').system('true')", 4500)
        self.assertTrue(car_rental.is_valid_plate("KA01AB1234"))
        self.assertFalse(car_rental.is_valid_plate("invalid"))
        with patch.dict(
            os.environ,
            {
                "CAR_RENTAL_ADMIN_USER": "administrator",
                "CAR_RENTAL_ADMIN_PASSWORD": "test-secret",
            },
        ):
            self.assertTrue(
                car_rental.admin_login("administrator", "test-secret")
            )
            self.assertFalse(
                car_rental.admin_login("administrator", "wrong")
            )
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(
                car_rental.admin_login("administrator", "test-secret")
            )

    def test_receipt_content_and_private_permissions(self) -> None:
        booking = {
            "code": "BK-TEST",
            "plate": "KA01AB1234",
            "customer": "O'Neil",
            "days": 3,
            "cost": 4500,
            "returned": False,
        }
        receipt_path = Path(car_rental.write_receipt(booking))
        try:
            self.assertEqual(
                receipt_path.read_text(encoding="utf-8"),
                "Booking BK-TEST: KA01AB1234 for 3 days = Rs.4500\n",
            )
            permissions = stat.S_IMODE(receipt_path.stat().st_mode)
            self.assertEqual(permissions & 0o077, 0)
        finally:
            receipt_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
