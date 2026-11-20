import pytest
import sqlite3
import os
import database

def test_database_initialization():
    database.init_db()
    summary = database.get_manifest_summary()
    assert summary["total_seats"] == 66
    assert summary["occupied_seats"] >= 0
    assert summary["available_seats"] <= 66

def test_get_all_seats():
    seats = database.get_all_seats()
    assert len(seats) == 66
    # Verify row 13 has seats A through F
    row13_seats = [s["seat_number"] for s in seats if s["seat_number"].startswith("13")]
    assert set(row13_seats) == {"13A", "13B", "13C", "13D", "13E", "13F"}

def test_student_lookup():
    # Test preloaded student
    student = database.get_student_by_uid("24BAI70262") # Ishleen
    assert student is not None
    assert student["student_name"] == "Ishleen"
    assert student["section"] == "24AML 6B"

def test_create_booking_and_double_booking_prevention():
    # Find an available seat
    available_info = database.get_available_seats()
    assert available_info["count"] > 0
    target_seat = available_info["available_seats"][0]

    # Use Ishleen for booking
    uid = "24BAI70262"
    success, msg, booking = database.create_booking(target_seat, uid, "ishleen@university.edu")
    assert success is True
    assert booking["seat_number"] == target_seat

    # Attempt to book the same seat with another student
    success2, msg2, _ = database.create_booking(target_seat, "24BAI70018", "harshit@university.edu")
    assert success2 is False
    assert "already been booked" in msg2.lower()

    # Attempt to book another seat with the same student (1 seat per student rule)
    other_seat = available_info["available_seats"][1]
    success3, msg3, _ = database.create_booking(other_seat, uid, "ishleen@university.edu")
    assert success3 is False
    assert "already holds a confirmed booking" in msg3.lower()

    # Cancel the booking
    booking_id = booking["booking_id"]
    cancelled, cancel_msg = database.cancel_booking(booking_id)
    assert cancelled is True
    assert "cancelled" in cancel_msg.lower()

    # Verify seat is available again
    seat_status = database.get_seat(target_seat)
    assert seat_status["status"] == "available"
