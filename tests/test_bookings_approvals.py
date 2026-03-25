from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient


def test_pending_approval_flow(client: TestClient) -> None:
    """Ensure a booking can be created, retrieved as pending, and approved."""
    start_date = date.today() + timedelta(days=365)
    end_date = start_date + timedelta(days=2)

    create_payload = {
        "customer": {"fullName": "Approval Tester", "email": f"approval.tester+{start_date.isoformat()}@example.com"},
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "requestedBy": "Approval Tester",
        "notes": "Automated approval test",
        "resourceId": "alder-lake-house",
    }

    create_response = client.post("/bookings", json=create_payload)
    assert create_response.status_code in (200, 201), create_response.text
    booking_id = create_response.json()["id"]

    pending_response = client.get("/bookings/pending", params={"resourceId": "alder-lake-house"})
    assert pending_response.status_code == 200, pending_response.text
    pending_ids = [item["id"] for item in pending_response.json()]
    assert booking_id in pending_ids

    decision_payload = {"actor": "Approver Bot", "note": "Approved via automated test"}
    approve_response = client.post(f"/bookings/{booking_id}/approve", json=decision_payload)
    assert approve_response.status_code == 200, approve_response.text

    after_response = client.get("/bookings/pending", params={"resourceId": "alder-lake-house"})
    assert after_response.status_code == 200, after_response.text
    remaining_ids = [item["id"] for item in after_response.json()]
    assert booking_id not in remaining_ids
