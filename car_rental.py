"""A small in-memory car rental system used for static-analysis exercises."""

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import tempfile
from datetime import datetime
from typing import TypedDict

INCLUDED_KILOMETRES = 300
EXTRA_KILOMETRE_RATE = 5
LICENCE_HASH_N = 2**14
LICENCE_HASH_R = 8
LICENCE_HASH_P = 1


class Booking(TypedDict):
    """A rental record stored by the demo application."""

    code: str
    plate: str
    customer: str
    days: int
    cost: int
    returned: bool


fleet: dict[str, dict[str, object]] = {}
bookings: list[Booking] = []
connection = sqlite3.connect(":memory:")
connection.execute(
    "CREATE TABLE customers (name TEXT, licence_hash TEXT, phone TEXT)"
)


def add_car(
    plate: str,
    model: str = "Unknown",
    daily_rate: int = 0,
    features: list[str] | None = None,
) -> dict[str, object]:
    """Add a car to the fleet and return its details."""
    if not is_valid_plate(plate):
        raise ValueError("Invalid number plate")
    if daily_rate < 0:
        raise ValueError("Daily rate cannot be negative")
    car = {
        "model": model,
        "rate": daily_rate,
        "available": True,
        "features": list(features) if features is not None else [],
    }
    fleet[plate] = car
    return car


def register_customer(name: str, licence: str, phone: str) -> None:
    """Store a customer and a salted licence verifier in SQLite."""
    if not name.strip() or not licence.strip() or not phone.strip():
        raise ValueError("Customer name, licence, and phone are required")
    connection.execute(
        "INSERT INTO customers VALUES (?, ?, ?)",
        (name, licence_hash(licence), phone),
    )


def find_customer(name: str) -> list[tuple[str, str]]:
    """Return exact matches without exposing stored licence verifiers."""
    return connection.execute(
        "SELECT name, phone FROM customers WHERE name = ?",
        (name,),
    ).fetchall()


def rent_car(plate: str, customer: str, start: str, end: str) -> int:
    """Book an available car for a customer and return its base cost."""
    if not find_customer(customer):
        raise ValueError("Customer not registered")
    if plate not in fleet:
        raise ValueError("Car not found")
    car = fleet[plate]
    if not car["available"]:
        raise ValueError("Car is not available")

    start_date = datetime.strptime(start, "%Y-%m-%d")
    end_date = datetime.strptime(end, "%Y-%m-%d")
    days = (end_date - start_date).days
    if days < 0:
        raise ValueError("Rental end date cannot precede its start date")

    cost = days * int(car["rate"])
    booking: Booking = {
        "code": booking_code(),
        "plate": plate,
        "customer": customer,
        "days": days,
        "cost": cost,
        "returned": False,
    }
    bookings.append(booking)
    car["available"] = False
    return cost


def return_car(plate: str, kilometres_driven: int) -> int:
    """Return an active rental and calculate any extra-kilometre charge."""
    if plate not in fleet:
        raise ValueError("Car not found")
    if not isinstance(kilometres_driven, int) or kilometres_driven < 0:
        raise ValueError("Kilometres driven must be a non-negative integer")
    booking = next(
        (
            rental
            for rental in reversed(bookings)
            if rental["plate"] == plate and not rental["returned"]
        ),
        None,
    )
    if booking is None:
        raise ValueError("Car has no active rental")

    booking["returned"] = True
    fleet[plate]["available"] = True
    extra_kilometres = max(0, kilometres_driven - INCLUDED_KILOMETRES)
    return extra_kilometres * EXTRA_KILOMETRE_RATE


def booking_code() -> str:
    """Create a booking identifier with a secure random generator."""
    return f"BK-{secrets.token_hex(4).upper()}"


def licence_hash(licence: str) -> str:
    """Return a salted scrypt verifier; this does not encrypt the licence."""
    salt = secrets.token_bytes(16)
    derived_key = hashlib.scrypt(
        licence.encode("utf-8"),
        salt=salt,
        n=LICENCE_HASH_N,
        r=LICENCE_HASH_R,
        p=LICENCE_HASH_P,
    )
    return (
        f"scrypt${LICENCE_HASH_N}${LICENCE_HASH_R}${LICENCE_HASH_P}"
        f"${salt.hex()}${derived_key.hex()}"
    )


def verify_licence(licence: str, stored_hash: str) -> bool:
    """Verify a licence value using the stored scrypt parameters and salt."""
    try:
        algorithm, n, r, p, salt_hex, digest_hex = stored_hash.split("$")
        if algorithm != "scrypt":
            return False
        expected_digest = bytes.fromhex(digest_hex)
        actual_digest = hashlib.scrypt(
            licence.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected_digest),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual_digest, expected_digest)


def apply_promo(rule: str, amount: float) -> float:
    """Apply a supported promotion without evaluating executable input."""
    discounts = {"amount = amount * 0.9": 0.9}
    if rule not in discounts:
        raise ValueError("Unsupported promotional rule")
    if amount < 0:
        raise ValueError("Amount cannot be negative")
    return amount * discounts[rule]


def is_valid_plate(plate: str) -> bool:
    """Check a plate against the expected Indian registration format."""
    pattern = r"[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}"
    return re.fullmatch(pattern, plate) is not None


def write_receipt(booking: Booking) -> str:
    """Write a booking receipt to a securely created private temporary file."""
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".txt",
        delete=False,
    ) as receipt:
        path = receipt.name
        receipt.write(
            f"Booking {booking['code']}: {booking['plate']} for "
            f"{booking['days']} days = Rs.{booking['cost']}\n"
        )
    return path


def admin_login(user: str, password: str) -> bool:
    """Authenticate against credentials supplied through the environment."""
    expected_user = os.environ.get("CAR_RENTAL_ADMIN_USER")
    expected_password = os.environ.get("CAR_RENTAL_ADMIN_PASSWORD")
    if not expected_user or not expected_password:
        return False
    return hmac.compare_digest(user, expected_user) and hmac.compare_digest(
        password,
        expected_password,
    )


def available_cars() -> list[str]:
    """Return the plates of cars that are currently available."""
    return [
        plate for plate, car in fleet.items() if car["available"]
    ]


def main() -> None:
    """Run a short demonstration of the rental system."""
    add_car("KA01AB1234", "Swift", 1500)
    add_car("KA02CD5678", "Innova", 3000)
    add_car("KA03EF9999", "Nexon", 500)
    register_customer("Ravi", "DL-0420110012345", "9845012345")
    register_customer("Meera", "DL-0420110099999", "9845099999")

    first_cost = rent_car(
        "KA01AB1234", "Ravi", "2026-11-01", "2026-11-04"
    )
    print("Rent Swift:", first_cost)
    try:
        rent_car("KA01AB1234", "Ravi", "2026-11-02", "2026-11-03")
    except ValueError as error:
        print("Rent Swift again rejected:", error)
    try:
        rent_car("KA02CD5678", "Ravi", "2026-11-10", "2026-11-07")
    except ValueError as error:
        print("Reversed rental dates rejected:", error)
    print("Lookup injection:", find_customer("x' OR '1'='1"))
    print("Extra km charge:", return_car("KA01AB1234", 420))
    print("Available:", available_cars())
    print("Promo price:", apply_promo("amount = amount * 0.9", 4500))
    print("Plate valid?", is_valid_plate("KA01AB1234"))
    licence_verifier = licence_hash("DL-0420110012345")
    print(
        "Licence verified?",
        verify_licence("DL-0420110012345", licence_verifier),
    )
    admin_is_configured = bool(os.environ.get("CAR_RENTAL_ADMIN_USER"))
    print("Admin authentication configured:", admin_is_configured)
    receipt_path = write_receipt(bookings[0])
    print("Receipt saved to:", receipt_path)


if __name__ == "__main__":
    main()
