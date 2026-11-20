import pytest
import json
from app import app
import database

@pytest.fixture
def client():
    app.config["TESTING"] = True
    database.init_db()
    with app.test_client() as client:
        yield client

def test_api_seats(client):
    response = client.get("/api/seats")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["total_seats"] == 66
    assert len(data["seats"]) == 66

def test_verify_student_valid(client):
    response = client.get("/api/students/verify/24BAI70262") # Ishleen
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["student"]["student_name"] == "Ishleen"

def test_verify_student_invalid(client):
    response = client.get("/api/students/verify/FAKEUID123")
    assert response.status_code == 404
    data = response.get_json()
    assert data["success"] is False

def test_booking_workflow(client):
    # 1. Get available seats
    seats_res = client.get("/api/seats")
    seats_data = seats_res.get_json()
    available_seats = [s["seat_number"] for s in seats_data["seats"] if not s["booked"]]
    assert len(available_seats) > 0
    test_seat = available_seats[0]

    # 2. Book seat with student Nipun (24BAI70635)
    booking_res = client.post("/api/bookings", json={
        "seat_number": test_seat,
        "uid": "24BAI70635",
        "email": "nipun@university.edu"
    })
    assert booking_res.status_code == 201
    booking_data = booking_res.get_json()
    assert booking_data["success"] is True
    created_booking = booking_data["bookings"][0]
    booking_id = created_booking["booking_id"]

    # 3. Prevent duplicate booking of same seat
    dup_res = client.post("/api/bookings", json={
        "seat_number": test_seat,
        "uid": "24BAI70316",
        "email": "bhavya@university.edu"
    })
    assert dup_res.status_code == 409
    assert dup_res.get_json()["success"] is False

    # 4. Prevent duplicate booking by same student
    other_seat = available_seats[1]
    student_dup_res = client.post("/api/bookings", json={
        "seat_number": other_seat,
        "uid": "24BAI70635",
        "email": "nipun@university.edu"
    })
    assert student_dup_res.status_code == 409
    assert student_dup_res.get_json()["success"] is False

    # 5. Cancel reservation
    del_res = client.delete(f"/api/bookings/{booking_id}")
    assert del_res.status_code == 200
    assert del_res.get_json()["success"] is True

def test_admin_summary_api(client):
    res = client.get("/api/admin/summary")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["summary"]["total_seats"] == 66

def test_template_routes(client):
    res_index = client.get("/")
    assert res_index.status_code == 200
    assert b"Campus Express" in res_index.data
    assert b"ExpressAI" in res_index.data

    res_admin = client.get("/admin")
    assert res_admin.status_code == 200
    assert b"Admin Dashboard" in res_admin.data

def test_admin_reset_security(client):
    # Invalid password
    bad_res = client.post("/api/admin/reset", json={"password": "WRONG_PASSWORD"})
    assert bad_res.status_code == 403
    assert bad_res.get_json()["success"] is False

    # Valid password
    good_res = client.post("/api/admin/reset", json={"password": "AMRITSAR1234"})
    assert good_res.status_code == 200
    assert good_res.get_json()["success"] is True

def test_admin_ai_summary_endpoint(client):
    res = client.post("/api/admin/ai-summary")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "ai_summary" in data

def test_ai_chat_endpoint(client):
    res = client.post("/api/ai/chat", json={
        "message": "How many seats are left on the bus?"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "response" in data
    assert len(data["response"]) > 0

