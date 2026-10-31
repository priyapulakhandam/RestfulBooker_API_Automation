"""Pydantic models for Restful-Booker API data validation."""
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class BookingDates(BaseModel):
    """Booking dates nested model."""
    model_config = ConfigDict(extra="ignore")

    checkin: str = Field(..., description="Check-in date in YYYY-MM-DD format")
    checkout: str = Field(..., description="Check-out date in YYYY-MM-DD format")


class BookingPayload(BaseModel):
    """Booking request body schema."""
    model_config = ConfigDict(extra="ignore")

    firstname: str = Field(..., min_length=1)
    lastname: str = Field(..., min_length=1)
    totalprice: int = Field(..., ge=0)
    depositpaid: bool
    bookingdates: BookingDates
    additionalneeds: Optional[str] = None


class BookingResponse(BookingPayload):
    """Model representing booking data returned by GET and PUT endpoints."""
    pass


class CreateBookingResponse(BaseModel):
    """Model representing response from POST /booking."""
    model_config = ConfigDict(extra="ignore")

    bookingid: int = Field(..., gt=0)
    booking: BookingResponse


class AuthRequest(BaseModel):
    """Authentication request credentials."""
    username: str
    password: str


class AuthResponse(BaseModel):
    """Authentication response model."""
    model_config = ConfigDict(extra="ignore")

    token: Optional[str] = None
    reason: Optional[str] = None
