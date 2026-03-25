from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .models import BookingStatus


class CustomerBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., alias="fullName", max_length=255)

    model_config = ConfigDict(populate_by_name=True)


class CustomerCreate(CustomerBase):
    pass


class CustomerRead(CustomerBase):
    id: int
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class BookingCreate(BaseModel):
    customer: CustomerCreate
    start_at: date = Field(..., alias="startDate")
    end_at: date = Field(..., alias="endDate")
    requested_by: str = Field(..., alias="requestedBy", max_length=120)
    notes: str | None = None
    resource_id: str = Field(default="alder-lake-house", alias="resourceId")
    amount: float | None = Field(default=None, ge=0)

    model_config = ConfigDict(populate_by_name=True)


class BookingRead(BaseModel):
    id: int
    resource_id: str = Field(..., alias="resourceId")
    status: BookingStatus
    start_at: date = Field(..., alias="startDate")
    end_at: date = Field(..., alias="endDate")
    requested_by: str = Field(..., alias="requestedBy")
    approved_by: str | None = Field(None, alias="approvedBy")
    notes: str | None = None
    amount: float | None = None
    approved_at: datetime | None = Field(None, alias="approvedAt")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")
    customer: CustomerRead

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class BookingDecision(BaseModel):
    actor: str = Field(..., alias="actor", max_length=120)
    note: str | None = Field(default=None, alias="note")

    model_config = ConfigDict(populate_by_name=True)


class CalendarBookingSummary(BaseModel):
    id: int
    customer_name: str = Field(..., alias="customerName")
    status: BookingStatus
    window_label: str = Field(..., alias="windowLabel")
    requested_by: str = Field(..., alias="requestedBy")
    notes: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class CalendarDay(BaseModel):
    iso: str
    day_label: str | None = Field(None, alias="dayLabel")
    is_current_month: bool = Field(..., alias="isCurrentMonth")
    is_today: bool = Field(False, alias="isToday")
    is_full: bool | None = Field(None, alias="isFull")
    is_unavailable: bool | None = Field(None, alias="isUnavailable")
    pending_count: int = Field(0, alias="pendingCount")
    remaining_slots: int = Field(0, alias="remainingSlots")
    bookings: list[CalendarBookingSummary] = Field(default_factory=list, alias="bookings")

    model_config = ConfigDict(populate_by_name=True)


class CalendarMonth(BaseModel):
    month_label: str = Field(..., alias="monthLabel")
    selected_iso: str = Field(..., alias="selectedIso")
    total_bookings: int = Field(0, alias="totalBookings")
    pending_count: int = Field(0, alias="pendingCount")
    remaining_slots: int = Field(0, alias="remainingSlots")
    next_available_label: str | None = Field(None, alias="nextAvailableLabel")
    updated_label: str | None = Field(None, alias="updatedLabel")
    weekday_labels: list[str] = Field(..., alias="weekdayLabels")
    weeks: list[list[CalendarDay]]

    model_config = ConfigDict(populate_by_name=True)


class CalendarDayDetail(BaseModel):
    iso: str
    date_label: str = Field(..., alias="dateLabel")
    summary: str | None = None
    confirmed_count: int = Field(0, alias="confirmedCount")
    pending_count: int = Field(0, alias="pendingCount")
    remaining_slots: int = Field(0, alias="remainingSlots")
    bookings: list[CalendarBookingSummary]

    model_config = ConfigDict(populate_by_name=True)


class PendingRequestSummary(BaseModel):
    id: int
    customer_name: str = Field(..., alias="customerName")
    date: str
    date_label: str = Field(..., alias="dateLabel")
    window_label: str = Field(..., alias="windowLabel")
    requested_by: str = Field(..., alias="requestedBy")
    notes: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class ResourceSummary(BaseModel):
    id: str
    name: str
    display_name: str = Field(..., alias="displayName")

    model_config = ConfigDict(populate_by_name=True)


class CalendarResponse(BaseModel):
    resource: ResourceSummary
    calendar: CalendarMonth
    selected_day: CalendarDayDetail | None = Field(None, alias="selectedDay")
    pending_requests: list[PendingRequestSummary] = Field(default_factory=list, alias="pendingRequests")

    model_config = ConfigDict(populate_by_name=True)
