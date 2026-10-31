"""Dynamic test data factory for Restful-Booker API tests."""
from datetime import datetime, timedelta
import random
from faker import Faker
from models.booking import BookingPayload, BookingDates

fake = Faker()


class BookingDataFactory:
    """Generates dynamic, realistic booking payloads."""

    @staticmethod
    def create_booking_payload(
        firstname: str = None,
        lastname: str = None,
        totalprice: int = None,
        depositpaid: bool = None,
        checkin_offset_days: int = 5,
        stay_duration_days: int = 4,
        additionalneeds: str = None,
    ) -> dict:
        """Create a randomized valid booking payload dictionary."""
        today = datetime.now()
        checkin_date = today + timedelta(days=checkin_offset_days)
        checkout_date = checkin_date + timedelta(days=stay_duration_days)

        payload = {
            "firstname": firstname or fake.first_name(),
            "lastname": lastname or fake.last_name(),
            "totalprice": totalprice if totalprice is not None else random.randint(100, 1000),
            "depositpaid": depositpaid if depositpaid is not None else random.choice([True, False]),
            "bookingdates": {
                "checkin": checkin_date.strftime("%Y-%m-%d"),
                "checkout": checkout_date.strftime("%Y-%m-%d"),
            },
            "additionalneeds": additionalneeds or random.choice(["Breakfast", "Late Checkout", "Airport Shuttle", "Crib"]),
        }
        return payload

    @staticmethod
    def create_updated_payload(original_payload: dict, **overrides) -> dict:
        """Generate an updated booking payload based on an original one."""
        updated = dict(original_payload)
        updated["firstname"] = overrides.get("firstname", f"Updated_{fake.first_name()}")
        updated["lastname"] = overrides.get("lastname", f"Updated_{fake.last_name()}")
        updated["totalprice"] = overrides.get("totalprice", original_payload.get("totalprice", 100) + 150)
        updated["depositpaid"] = overrides.get("depositpaid", not original_payload.get("depositpaid", True))

        # Push checkout by another 3 days
        if "bookingdates" not in overrides:
            curr_checkin = original_payload["bookingdates"]["checkin"]
            curr_checkout = datetime.strptime(original_payload["bookingdates"]["checkout"], "%Y-%m-%d")
            new_checkout = curr_checkout + timedelta(days=3)
            updated["bookingdates"] = {
                "checkin": curr_checkin,
                "checkout": new_checkout.strftime("%Y-%m-%d"),
            }
        else:
            updated["bookingdates"] = overrides["bookingdates"]

        updated["additionalneeds"] = overrides.get("additionalneeds", "Dinner & Spa")
        return updated
