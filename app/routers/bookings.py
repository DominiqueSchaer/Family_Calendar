from __future__ import annotations

from calendar import Calendar, monthrange
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Iterable

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .. import models, schemas
from ..database import get_db

router = APIRouter(tags=["bookings"])

DEFAULT_RESOURCE_ID = "alder-lake-house"
DEFAULT_RESOURCE_NAME = "alder-lake-house"
DEFAULT_RESOURCE_DISPLAY_NAME = "Riederalp"
CAPACITY_PER_DAY = 1
WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _daterange(start: date, end: date) -> Iterable[date]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


async def _upsert_customer(db: AsyncSession, payload: schemas.CustomerCreate) -> models.Customer:
    normalized_email = payload.email.lower()
    stmt = select(models.Customer).where(models.Customer.email == normalized_email)
    result = await db.execute(stmt)
    customer = result.scalar_one_or_none()
    if customer is None:
        customer = models.Customer(email=normalized_email, full_name=payload.full_name)
        db.add(customer)
        await db.flush()
    else:
        customer.full_name = payload.full_name
    return customer


async def _ensure_no_conflict(
    db: AsyncSession,
    *,
    resource_id: str,
    start_at: date,
    end_at: date,
    exclude_booking_id: int | None = None,
) -> None:
    stmt = (
        select(models.Booking)
        .where(models.Booking.resource_id == resource_id)
        .where(models.Booking.status == models.BookingStatus.approved)
        .where(models.Booking.end_at >= start_at)
        .where(models.Booking.start_at <= end_at)
    )
    if exclude_booking_id is not None:
        stmt = stmt.where(models.Booking.id != exclude_booking_id)
    result = await db.execute(stmt.limit(1))
    conflict = result.scalar_one_or_none()
    if conflict is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Booking overlaps an approved reservation")


def _format_window_label(booking: models.Booking) -> str:
    if booking.start_at == booking.end_at:
        return booking.start_at.strftime("%a, %d %b %Y")
    return f"{booking.start_at.strftime('%d %b %Y')} - {booking.end_at.strftime('%d %b %Y')}"


def _booking_summary(booking: models.Booking) -> schemas.CalendarBookingSummary:
    return schemas.CalendarBookingSummary(
        id=booking.id,
        customerName=booking.customer.full_name,
        status=booking.status,
        windowLabel=_format_window_label(booking),
        requestedBy=booking.requested_by,
        notes=booking.notes,
    )


def _pending_request_summary(booking: models.Booking) -> schemas.PendingRequestSummary:
    return schemas.PendingRequestSummary(
        id=booking.id,
        customerName=booking.customer.full_name,
        date=booking.start_at.isoformat(),
        dateLabel=booking.start_at.strftime("%a, %d %b"),
        windowLabel=_format_window_label(booking),
        requestedBy=booking.requested_by,
        notes=booking.notes,
    )


def _resource_summary(resource_id: str) -> schemas.ResourceSummary:
    if resource_id == DEFAULT_RESOURCE_ID:
        name = DEFAULT_RESOURCE_NAME
        display_name = DEFAULT_RESOURCE_DISPLAY_NAME
    else:
        name = resource_id
        display_name = resource_id.replace("-", " ").title()
    return schemas.ResourceSummary(id=resource_id, name=name, displayName=display_name)


def _month_anchor(month: str | None) -> date:
    if not month:
        today = date.today()
        return date(today.year, today.month, 1)
    try:
        year, month_number = map(int, month.split("-"))
        return date(year, month_number, 1)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid month format") from exc


async def _fetch_bookings_for_range(
    db: AsyncSession,
    *,
    resource_id: str,
    start_at: date,
    end_at: date,
) -> list[models.Booking]:
    stmt = (
        select(models.Booking)
        .options(joinedload(models.Booking.customer))
        .where(models.Booking.resource_id == resource_id)
        .where(models.Booking.end_at >= start_at)
        .where(models.Booking.start_at <= end_at)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


def _build_day_detail(day: date, bookings: list[models.Booking]) -> schemas.CalendarDayDetail:
    approved_count = sum(1 for booking in bookings if booking.status == models.BookingStatus.approved)
    pending_count = sum(1 for booking in bookings if booking.status == models.BookingStatus.pending)
    remaining_slots = max(0, CAPACITY_PER_DAY - approved_count)

    if approved_count >= CAPACITY_PER_DAY:
        summary = "All slots are filled. Decline or reschedule requests to reopen capacity."
    elif bookings:
        summary = "Review guest details, confirm approvals, or release slots as needed."
    else:
        summary = "Wide open day ready for a new booking."

    return schemas.CalendarDayDetail(
        iso=day.isoformat(),
        dateLabel=day.strftime("%A, %d %B %Y"),
        summary=summary,
        confirmedCount=approved_count,
        pendingCount=pending_count,
        remainingSlots=remaining_slots,
        bookings=[_booking_summary(booking) for booking in sorted(bookings, key=lambda b: (b.start_at, b.id))],
    )


def _build_calendar(
    *,
    anchor: date,
    resource_id: str,
    bookings: list[models.Booking],
    selected_date: date | None,
) -> schemas.CalendarResponse:
    cal = Calendar(firstweekday=0)
    weeks_dates = cal.monthdatescalendar(anchor.year, anchor.month)
    grid_start = weeks_dates[0][0]
    grid_end = weeks_dates[-1][-1]

    bookings_by_day: dict[date, list[models.Booking]] = {}
    for booking in bookings:
        span_start = max(booking.start_at, grid_start)
        span_end = min(booking.end_at, grid_end)
        for day_value in _daterange(span_start, span_end):
            bookings_by_day.setdefault(day_value, []).append(booking)

    month_start = anchor
    month_end = date(anchor.year, anchor.month, monthrange(anchor.year, anchor.month)[1])
    total_bookings = len(
        {
            booking.id
            for booking in bookings
            if booking.status in {models.BookingStatus.pending, models.BookingStatus.approved}
            and booking.start_at <= month_end
            and booking.end_at >= month_start
        }
    )
    total_pending = len(
        {
            booking.id
            for booking in bookings
            if booking.status == models.BookingStatus.pending
            and booking.start_at <= month_end
            and booking.end_at >= month_start
        }
    )

    weeks_payload: list[list[schemas.CalendarDay]] = []
    total_remaining = 0

    today = date.today()
    selected = selected_date or (today if anchor.year == today.year and anchor.month == today.month else anchor)

    for week in weeks_dates:
        week_payload: list[schemas.CalendarDay] = []
        for day_value in week:
            day_bookings = bookings_by_day.get(day_value, [])
            approved_count = sum(1 for booking in day_bookings if booking.status == models.BookingStatus.approved)
            pending_count = sum(1 for booking in day_bookings if booking.status == models.BookingStatus.pending)
            remaining_slots = max(0, CAPACITY_PER_DAY - approved_count)

            if day_value.month == anchor.month:
                total_remaining += remaining_slots

            week_payload.append(
                schemas.CalendarDay(
                    iso=day_value.isoformat(),
                    dayLabel=str(day_value.day),
                    isCurrentMonth=day_value.month == anchor.month,
                    isToday=day_value == today,
                    isFull=approved_count >= CAPACITY_PER_DAY,
                    isUnavailable=False,
                    pendingCount=pending_count,
                    remainingSlots=remaining_slots,
                    bookings=[_booking_summary(booking) for booking in sorted(day_bookings, key=lambda b: (b.start_at, b.id))],
                )
            )
        weeks_payload.append(week_payload)

    next_available_label = None
    for day_value in _daterange(max(today, grid_start), grid_end):
        day_bookings = bookings_by_day.get(day_value, [])
        approved_count = sum(1 for booking in day_bookings if booking.status == models.BookingStatus.approved)
        if approved_count < CAPACITY_PER_DAY:
            next_available_label = day_value.strftime("%a, %d %b %Y")
            break

    if selected < grid_start or selected > grid_end:
        selected = anchor
    selected_detail = _build_day_detail(selected, bookings_by_day.get(selected, []))

    pending_requests = [
        _pending_request_summary(booking)
        for booking in sorted(
            (b for b in bookings if b.status == models.BookingStatus.pending),
            key=lambda b: (b.start_at, b.id),
        )
    ]

    calendar_payload = schemas.CalendarMonth(
        monthLabel=anchor.strftime("%B %Y"),
        selectedIso=selected.isoformat(),
        totalBookings=total_bookings,
        pendingCount=total_pending,
        remainingSlots=total_remaining,
        nextAvailableLabel=next_available_label,
        updatedLabel=datetime.now(timezone.utc).strftime("Updated %d %b %Y %H:%M UTC"),
        weekdayLabels=WEEKDAY_LABELS,
        weeks=weeks_payload,
    )

    return schemas.CalendarResponse(
        resource=_resource_summary(resource_id),
        calendar=calendar_payload,
        selectedDay=selected_detail,
        pendingRequests=pending_requests,
    )


def _booking_read(booking: models.Booking) -> schemas.BookingRead:
    return schemas.BookingRead.model_validate(booking, from_attributes=True)


@router.get("/bookings", response_model=list[schemas.BookingRead])
async def list_bookings(
    *,
    db: AsyncSession = Depends(get_db),
    status_filter: models.BookingStatus | None = Query(None, alias="status"),
    resource_id: str = Query(DEFAULT_RESOURCE_ID, alias="resourceId"),
    start_date: date | None = Query(None, alias="startDate"),
    end_date: date | None = Query(None, alias="endDate"),
) -> list[schemas.BookingRead]:
    stmt = (
        select(models.Booking)
        .options(joinedload(models.Booking.customer))
        .where(models.Booking.resource_id == resource_id)
        .order_by(models.Booking.start_at.asc(), models.Booking.id.asc())
    )
    if status_filter is not None:
        stmt = stmt.where(models.Booking.status == status_filter)
    if start_date is not None:
        stmt = stmt.where(models.Booking.end_at >= start_date)
    if end_date is not None:
        stmt = stmt.where(models.Booking.start_at <= end_date)

    result = await db.execute(stmt)
    records = result.scalars().all()
    return [_booking_read(booking) for booking in records]


@router.post("/bookings", response_model=schemas.BookingRead, status_code=status.HTTP_201_CREATED)
async def create_booking(*, db: AsyncSession = Depends(get_db), payload: schemas.BookingCreate) -> schemas.BookingRead:
    if payload.start_at > payload.end_at:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="End date must be on or after start date")

    customer = await _upsert_customer(db, payload.customer)
    await _ensure_no_conflict(
        db,
        resource_id=payload.resource_id,
        start_at=payload.start_at,
        end_at=payload.end_at,
    )

    amount_value = Decimal(str(payload.amount)) if payload.amount is not None else None

    booking = models.Booking(
        customer_id=customer.id,
        resource_id=payload.resource_id,
        status=models.BookingStatus.pending,
        start_at=payload.start_at,
        end_at=payload.end_at,
        requested_by=payload.requested_by,
        notes=payload.notes,
        amount=amount_value,
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return _booking_read(booking)


async def _get_booking(db: AsyncSession, booking_id: int) -> models.Booking:
    stmt = (
        select(models.Booking)
        .options(joinedload(models.Booking.customer))
        .where(models.Booking.id == booking_id)
    )
    result = await db.execute(stmt)
    booking = result.scalar_one_or_none()
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return booking


@router.post("/bookings/{booking_id}/approve", response_model=schemas.BookingRead)
async def approve_booking(
    *,
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    payload: schemas.BookingDecision,
) -> schemas.BookingRead:
    booking = await _get_booking(db, booking_id)
    if booking.status != models.BookingStatus.pending:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only pending bookings can be approved")

    await _ensure_no_conflict(
        db,
        resource_id=booking.resource_id,
        start_at=booking.start_at,
        end_at=booking.end_at,
        exclude_booking_id=booking.id,
    )

    booking.status = models.BookingStatus.approved
    booking.approved_by = payload.actor
    booking.approved_at = datetime.now(timezone.utc)
    if payload.note:
        booking.notes = f"{booking.notes}\nDecision: {payload.note}" if booking.notes else payload.note

    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return _booking_read(booking)


@router.post("/bookings/{booking_id}/decline", response_model=schemas.BookingRead)
async def decline_booking(
    *,
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    payload: schemas.BookingDecision,
) -> schemas.BookingRead:
    booking = await _get_booking(db, booking_id)
    if booking.status != models.BookingStatus.pending:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only pending bookings can be declined")

    booking.status = models.BookingStatus.declined
    booking.approved_by = payload.actor
    booking.approved_at = datetime.now(timezone.utc)
    if payload.note:
        booking.notes = f"{booking.notes}\nDecision: {payload.note}" if booking.notes else payload.note

    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return _booking_read(booking)


@router.delete("/bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booking(
    *,
    booking_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    booking = await _get_booking(db, booking_id)
    await db.delete(booking)
    await db.commit()


@router.get("/calendar", response_model=schemas.CalendarResponse)
async def get_calendar(
    *,
    db: AsyncSession = Depends(get_db),
    month: str | None = Query(None),
    selected_date: date | None = Query(None, alias="selectedDate"),
    resource_id: str = Query(DEFAULT_RESOURCE_ID, alias="resourceId"),
) -> schemas.CalendarResponse:
    anchor = _month_anchor(month)
    cal = Calendar(firstweekday=0)
    weeks = cal.monthdatescalendar(anchor.year, anchor.month)
    grid_start = weeks[0][0]
    grid_end = weeks[-1][-1]

    bookings = await _fetch_bookings_for_range(db, resource_id=resource_id, start_at=grid_start, end_at=grid_end)
    return _build_calendar(anchor=anchor, resource_id=resource_id, bookings=bookings, selected_date=selected_date)


@router.get("/calendar/day", response_model=schemas.CalendarDayDetail)
async def get_calendar_day(
    *,
    db: AsyncSession = Depends(get_db),
    date_value: date = Query(..., alias="date"),
    resource_id: str = Query(DEFAULT_RESOURCE_ID, alias="resourceId"),
) -> schemas.CalendarDayDetail:
    bookings = await _fetch_bookings_for_range(
        db,
        resource_id=resource_id,
        start_at=date_value,
        end_at=date_value,
    )
    day_bookings = [booking for booking in bookings if booking.start_at <= date_value <= booking.end_at]
    return _build_day_detail(date_value, day_bookings)


@router.get("/bookings/pending", response_model=list[schemas.PendingRequestSummary])
async def list_pending_bookings(
    *,
    db: AsyncSession = Depends(get_db),
    resource_id: str = Query(DEFAULT_RESOURCE_ID, alias="resourceId"),
) -> list[schemas.PendingRequestSummary]:
    stmt = (
        select(models.Booking)
        .options(joinedload(models.Booking.customer))
        .where(models.Booking.resource_id == resource_id)
        .where(models.Booking.status == models.BookingStatus.pending)
        .order_by(models.Booking.start_at.asc(), models.Booking.id.asc())
    )
    result = await db.execute(stmt)
    bookings = result.scalars().all()
    return [_pending_request_summary(booking) for booking in bookings]
