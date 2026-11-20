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
    response = client.get("/api/students/verify/DEMO0001") # Demo Student
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["student"]["student_name"] == "Demo Student"

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

    # 2. Book seat with student Demo Student (DEMO0002)
    booking_res = client.post("/api/bookings", json={
        "seat_number": test_seat,
        "uid": "DEMO0002",
        "email": "student@example.invalid"
    })
    assert booking_res.status_code == 201
    booking_data = booking_res.get_json()
    assert booking_data["success"] is True
    created_booking = booking_data["bookings"][0]
    booking_id = created_booking["booking_id"]

    # 3. Prevent duplicate booking of same seat
    dup_res = client.post("/api/bookings", json={
        "seat_number": test_seat,
        "uid": "DEMO0003",
        "email": "student@example.invalid"
    })
    assert dup_res.status_code == 409
    assert dup_res.get_json()["success"] is False

    # 4. Prevent duplicate booking by same student
    other_seat = available_seats[1]
    student_dup_res = client.post("/api/bookings", json={
        "seat_number": other_seat,
        "uid": "DEMO0002",
        "email": "student@example.invalid"
    })
    assert student_dup_res.status_code == 409
    assert student_dup_res.get_json()["success"] is False

    # 5. Cancel reservation
    login_res = client.post("/api/admin/login", json={"password": app.config["ADMIN_PASSWORD"]})
    assert login_res.status_code == 200
    del_res = client.delete(f"/api/bookings/{booking_id}")
    assert del_res.status_code == 200
    assert del_res.get_json()["success"] is True

def test_admin_summary_api(client):
    login_res = client.post("/api/admin/login", json={"password": app.config["ADMIN_PASSWORD"]})
    assert login_res.status_code == 200
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
    # Admin routes require a successful sign-in.
    unauthenticated_res = client.post("/api/admin/reset", json={})
    assert unauthenticated_res.status_code == 401

    bad_res = client.post("/api/admin/login", json={"password": "WRONG_PASSWORD"})
    assert bad_res.status_code == 401
    assert bad_res.get_json()["success"] is False

    good_res = client.post("/api/admin/login", json={"password": app.config["ADMIN_PASSWORD"]})
    assert good_res.status_code == 200
    reset_res = client.post("/api/admin/reset", json={})
    assert reset_res.status_code == 200
    assert reset_res.get_json()["success"] is True


def test_admin_manifest_requires_login(client):
    assert client.get("/api/bookings").status_code == 401
    assert client.get("/api/admin/summary").status_code == 401
    assert client.post("/api/admin/ai-summary").status_code == 401
    assert client.delete("/api/bookings/1").status_code == 401


def test_public_responses_omit_student_details(client):
    database.reset_all_bookings()
    response = client.get("/api/seats")
    assert response.status_code == 200
    seats = response.get_json()["seats"]
    assert all(set(seat) == {"seat_number", "booked"} for seat in seats)
    available_seat = next(seat["seat_number"] for seat in seats if not seat["booked"])

    booking = client.post("/api/bookings", json={
        "seat_number": available_seat,
        "uid": "DEMO0064",
        "email": "student@example.invalid"
    })
    assert booking.status_code == 201
    assert set(booking.get_json()["bookings"][0]) == {"booking_id", "seat_number"}


def test_admin_session_logout(client):
    login = client.post("/api/admin/login", json={"password": app.config["ADMIN_PASSWORD"]})
    assert login.status_code == 200
    assert client.get("/api/admin/session").get_json()["authenticated"] is True
    assert client.post("/api/admin/logout").status_code == 200
    assert client.get("/api/admin/session").get_json()["authenticated"] is False
    assert client.get("/api/bookings").status_code == 401

def test_admin_ai_summary_endpoint(client):
    login_res = client.post("/api/admin/login", json={"password": app.config["ADMIN_PASSWORD"]})
    assert login_res.status_code == 200
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

