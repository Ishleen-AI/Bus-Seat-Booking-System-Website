import sqlite3
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from config import Config

def get_db_path() -> str:
    db_path = Config.DATABASE_PATH
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    return db_path

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path(), timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# Initial seed data for registered students
PRELOADED_STUDENTS = [
    {
        "uid": f"DEMO{student_number:04d}",
        "name": "Demo Student",
        "section": "Demo",
        "phone": "",
    }
    for student_number in range(1, 65)
]

# Generate standard 66 seats layout
def generate_66_seats() -> List[Dict[str, Any]]:
    seat_list = []
    # Rows 1 to 12: 5 seats each (A, B, C, D, E) = 60 seats
    for r in range(1, 13):
        for col in ['A', 'B', 'C', 'D', 'E']:
            seat_list.append({
                "seat_number": f"{r}{col}",
                "row_num": r,
                "col_letter": col
            })
    # Back Row (Row 13): 6 seats (A, B, C, D, E, F) = 6 seats
    for col in ['A', 'B', 'C', 'D', 'E', 'F']:
        seat_list.append({
            "seat_number": f"13{col}",
            "row_num": 13,
            "col_letter": col
        })
    return seat_list

def init_db(seed_sample_bookings: bool = True):
    """Initializes tables and seeds initial data."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create students table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT NOT NULL,
        uid TEXT UNIQUE NOT NULL COLLATE NOCASE,
        section TEXT,
        phone TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create seats table (66 seats)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS seats (
        seat_id INTEGER PRIMARY KEY AUTOINCREMENT,
        seat_number TEXT UNIQUE NOT NULL COLLATE NOCASE,
        status TEXT NOT NULL DEFAULT 'available',
        row_num INTEGER,
        col_letter TEXT
    )
    """)

    # Create bookings table with transaction integrity
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL REFERENCES students(student_id),
        seat_id INTEGER NOT NULL REFERENCES seats(seat_id),
        booking_status TEXT NOT NULL DEFAULT 'confirmed',
        booking_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        entry_email TEXT,
        notes TEXT
    )
    """)

    # Create unique index to ensure at most ONE active booking per seat
    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_active_seat
    ON bookings(seat_id)
    WHERE booking_status = 'confirmed'
    """)

    # Create unique index to ensure at most ONE active booking per student
    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_active_student
    ON bookings(student_id)
    WHERE booking_status = 'confirmed'
    """)

    # Seed Students if empty
    cursor.execute("SELECT COUNT(*) FROM students")
    if cursor.fetchone()[0] == 0:
        for s in PRELOADED_STUDENTS:
            cursor.execute(
                "INSERT INTO students (student_name, uid, section, phone) VALUES (?, ?, ?, ?)",
                (s["name"], s["uid"].strip().upper(), s["section"], s["phone"])
            )

    # Seed Seats if empty
    cursor.execute("SELECT COUNT(*) FROM seats")
    if cursor.fetchone()[0] == 0:
        for s in generate_66_seats():
            cursor.execute(
                "INSERT INTO seats (seat_number, status, row_num, col_letter) VALUES (?, 'available', ?, ?)",
                (s["seat_number"], s["row_num"], s["col_letter"])
            )

    # Seed initial demo reservations (for demonstration purposes if requested)
    cursor.execute("SELECT COUNT(*) FROM bookings WHERE booking_status = 'confirmed'")
    if seed_sample_bookings and cursor.fetchone()[0] == 0:
        sample_bookings = [
            {"seat": "1A", "uid": "DEMO0061", "email": "admin@example.invalid"},
            {"seat": "1B", "uid": "DEMO0062", "email": "rep1@example.invalid"},
            {"seat": "3C", "uid": "DEMO0063", "email": "admin@example.invalid"},
            {"seat": "13F", "uid": "DEMO0064", "email": "rep2@example.invalid"}
        ]
        for b in sample_bookings:
            try:
                # Find student_id and seat_id
                cursor.execute("SELECT student_id FROM students WHERE uid = ?", (b["uid"],))
                student = cursor.fetchone()
                cursor.execute("SELECT seat_id FROM seats WHERE seat_number = ?", (b["seat"],))
                seat = cursor.fetchone()
                if student and seat:
                    cursor.execute(
                        "INSERT INTO bookings (student_id, seat_id, booking_status, entry_email) VALUES (?, ?, 'confirmed', ?)",
                        (student["student_id"], seat["seat_id"], b["email"])
                    )
                    cursor.execute(
                        "UPDATE seats SET status = 'booked' WHERE seat_id = ?",
                        (seat["seat_id"],)
                    )
            except Exception as e:
                print(f"Sample booking error for {b['seat']}: {e}")

    conn.commit()
    conn.close()

def get_all_seats() -> List[Dict[str, Any]]:
    """Returns all 66 seats with current status and active booking details."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
        s.seat_id,
        s.seat_number,
        s.status,
        s.row_num,
        s.col_letter,
        b.booking_id,
        b.booking_date,
        b.entry_email,
        st.student_id,
        st.student_name,
        st.uid,
        st.section,
        st.phone
    FROM seats s
    LEFT JOIN bookings b ON s.seat_id = b.seat_id AND b.booking_status = 'confirmed'
    LEFT JOIN students st ON b.student_id = st.student_id
    ORDER BY s.row_num ASC, s.col_letter ASC
    """)
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        is_booked = (r["status"] == "booked" and r["booking_id"] is not None)
        result.append({
            "seat_id": r["seat_id"],
            "seat_number": r["seat_number"],
            "status": "booked" if is_booked else "available",
            "booked": is_booked,
            "row_num": r["row_num"],
            "col_letter": r["col_letter"],
            "booking_id": r["booking_id"],
            "student_name": r["student_name"] or "",
            "uid": r["uid"] or "",
            "section": r["section"] or "",
            "phone": r["phone"] or "",
            "entry_email": r["entry_email"] or ""
        })
    return result

def get_seat(seat_number: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
        s.seat_id, s.seat_number, s.status, s.row_num, s.col_letter,
        b.booking_id, b.booking_date, b.entry_email,
        st.student_name, st.uid, st.section, st.phone
    FROM seats s
    LEFT JOIN bookings b ON s.seat_id = b.seat_id AND b.booking_status = 'confirmed'
    LEFT JOIN students st ON b.student_id = st.student_id
    WHERE s.seat_number = ? COLLATE NOCASE
    """, (seat_number.strip(),))
    r = cursor.fetchone()
    conn.close()
    if not r:
        return None
    is_booked = (r["status"] == "booked" and r["booking_id"] is not None)
    return {
        "seat_id": r["seat_id"],
        "seat_number": r["seat_number"],
        "status": "booked" if is_booked else "available",
        "booked": is_booked,
        "booking_id": r["booking_id"],
        "student_name": r["student_name"] or "",
        "uid": r["uid"] or "",
        "section": r["section"] or "",
        "phone": r["phone"] or ""
    }

def get_student_by_uid(uid: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE uid = ? COLLATE NOCASE", (uid.strip(),))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def add_student(name: str, uid: str, section: str = "", phone: str = "") -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO students (student_name, uid, section, phone) VALUES (?, ?, ?, ?)",
        (name.strip(), uid.strip().upper(), section.strip(), phone.strip())
    )
    student_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"student_id": student_id, "name": name, "uid": uid.upper(), "section": section, "phone": phone}

def create_booking(seat_number: str, uid: str, entry_email: str = "") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Creates a booking atomically.
    Ensures:
      - Valid student
      - Available seat
      - Student has not booked another seat
      - Commits transaction atomically
    """
    conn = get_db_connection()
    try:
        # Use IMMEDIATE transaction to lock database against concurrent writes
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()

        # 1. Verify student exists
        cursor.execute("SELECT student_id, student_name, uid, section, phone FROM students WHERE uid = ? COLLATE NOCASE", (uid.strip(),))
        student = cursor.fetchone()
        if not student:
            conn.rollback()
            return False, f"UID '{uid}' is not on the authorized student roster.", None

        student_id = student["student_id"]
        student_name = student["student_name"]

        # 2. Check if student already has an active confirmed booking
        cursor.execute("""
        SELECT b.booking_id, s.seat_number 
        FROM bookings b
        JOIN seats s ON b.seat_id = s.seat_id
        WHERE b.student_id = ? AND b.booking_status = 'confirmed'
        """, (student_id,))
        existing_booking = cursor.fetchone()
        if existing_booking:
            conn.rollback()
            return False, f"Student '{student_name}' ({uid}) already holds a confirmed booking for Seat {existing_booking['seat_number']}. Limit is one seat per student.", None

        # 3. Check seat exists and is currently available
        cursor.execute("SELECT seat_id, seat_number, status FROM seats WHERE seat_number = ? COLLATE NOCASE", (seat_number.strip(),))
        seat = cursor.fetchone()
        if not seat:
            conn.rollback()
            return False, f"Seat '{seat_number}' does not exist on this bus.", None

        if seat["status"] == "booked":
            conn.rollback()
            return False, f"Seat '{seat_number}' has already been booked by another passenger.", None

        seat_id = seat["seat_id"]

        # 4. Insert booking
        cursor.execute("""
        INSERT INTO bookings (student_id, seat_id, booking_status, entry_email)
        VALUES (?, ?, 'confirmed', ?)
        """, (student_id, seat_id, entry_email.strip()))
        booking_id = cursor.lastrowid

        # 5. Mark seat as booked
        cursor.execute("UPDATE seats SET status = 'booked' WHERE seat_id = ?", (seat_id,))

        conn.commit()

        booking_details = {
            "booking_id": booking_id,
            "seat_number": seat["seat_number"],
            "student_name": student_name,
            "uid": student["uid"],
            "section": student["section"],
            "phone": student["phone"],
            "entry_email": entry_email.strip()
        }
        return True, f"Successfully confirmed Seat {seat['seat_number']} for {student_name} ({uid}).", booking_details

    except sqlite3.IntegrityError as e:
        conn.rollback()
        return False, f"Booking conflict detected: {str(e)}", None
    except Exception as e:
        conn.rollback()
        return False, f"Database error during reservation: {str(e)}", None
    finally:
        conn.close()

def cancel_booking(booking_id: int) -> Tuple[bool, str]:
    """Cancels an active booking and frees the seat."""
    conn = get_db_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()

        cursor.execute("""
        SELECT b.booking_id, b.seat_id, s.seat_number, st.student_name 
        FROM bookings b
        JOIN seats s ON b.seat_id = s.seat_id
        JOIN students st ON b.student_id = st.student_id
        WHERE b.booking_id = ? AND b.booking_status = 'confirmed'
        """, (booking_id,))
        booking = cursor.fetchone()

        if not booking:
            conn.rollback()
            return False, f"No active confirmed booking found with ID {booking_id}."

        seat_id = booking["seat_id"]
        seat_number = booking["seat_number"]
        student_name = booking["student_name"]

        # Update booking status
        cursor.execute("UPDATE bookings SET booking_status = 'cancelled' WHERE booking_id = ?", (booking_id,))
        # Free the seat
        cursor.execute("UPDATE seats SET status = 'available' WHERE seat_id = ?", (seat_id,))

        conn.commit()
        return True, f"Booking #{booking_id} for Seat {seat_number} ({student_name}) has been cancelled."
    except Exception as e:
        conn.rollback()
        return False, f"Error cancelling booking: {str(e)}"
    finally:
        conn.close()

def reset_all_bookings() -> Tuple[bool, str, int]:
    """Resets all bookings and frees all 66 seats."""
    conn = get_db_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM bookings WHERE booking_status = 'confirmed'")
        count = cursor.fetchone()[0]

        cursor.execute("UPDATE bookings SET booking_status = 'cancelled' WHERE booking_status = 'confirmed'")
        cursor.execute("UPDATE seats SET status = 'available'")

        conn.commit()
        return True, f"Successfully reset all {count} active bookings. All 66 seats are now available.", count
    except Exception as e:
        conn.rollback()
        return False, f"Database error during bus reset: {str(e)}", 0
    finally:
        conn.close()

def get_all_bookings(active_only: bool = True) -> List[Dict[str, Any]]:
    """Returns booking manifest for admin dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT 
        b.booking_id,
        b.booking_status,
        b.booking_date,
        b.entry_email,
        s.seat_number,
        st.student_name,
        st.uid,
        st.section,
        st.phone
    FROM bookings b
    JOIN seats s ON b.seat_id = s.seat_id
    JOIN students st ON b.student_id = st.student_id
    """
    if active_only:
        query += " WHERE b.booking_status = 'confirmed' "
    query += " ORDER BY s.row_num ASC, s.col_letter ASC"

    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_available_seats() -> Dict[str, Any]:
    """Returns total available seats and list of seat identifiers."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT seat_number FROM seats WHERE status = 'available' ORDER BY row_num, col_letter")
    available = [r["seat_number"] for r in cursor.fetchall()]
    conn.close()
    return {
        "count": len(available),
        "available_seats": available,
        "sample": available[:10]  # First 10 available for prompt efficiency
    }

def get_booked_seats() -> Dict[str, Any]:
    """Returns total booked seats and list of seat identifiers."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT seat_number FROM seats WHERE status = 'booked' ORDER BY row_num, col_letter")
    booked = [r["seat_number"] for r in cursor.fetchall()]
    conn.close()
    return {
        "count": len(booked),
        "booked_seats": booked
    }

def get_manifest_summary() -> Dict[str, Any]:
    """Calculates statistics: occupancy rate, total seats, breakdown."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM seats")
    total_seats = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM seats WHERE status = 'booked'")
    occupied_seats = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM seats WHERE status = 'available'")
    available_seats = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bookings WHERE booking_status = 'cancelled'")
    cancelled_count = cursor.fetchone()[0]

    # Group by sections
    cursor.execute("""
    SELECT st.section, COUNT(*) as count
    FROM bookings b
    JOIN students st ON b.student_id = st.student_id
    WHERE b.booking_status = 'confirmed'
    GROUP BY st.section
    ORDER BY count DESC
    """)
    sections_breakdown = [dict(r) for r in cursor.fetchall()]

    conn.close()

    occupancy_rate = round((occupied_seats / total_seats * 100), 1) if total_seats > 0 else 0.0

    return {
        "total_seats": total_seats,
        "occupied_seats": occupied_seats,
        "available_seats": available_seats,
        "occupancy_rate": occupancy_rate,
        "cancelled_count": cancelled_count,
        "sections_breakdown": sections_breakdown
    }

def get_student_booking_info(query: str) -> Optional[Dict[str, Any]]:
    """Safe lookup for ExpressAI: returns sanitized student booking info without disclosing phone number."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Query could be UID or Seat Number
    cursor.execute("""
    SELECT 
        b.booking_id,
        b.booking_date,
        s.seat_number,
        st.student_name,
        st.uid,
        st.section
    FROM bookings b
    JOIN seats s ON b.seat_id = s.seat_id
    JOIN students st ON b.student_id = st.student_id
    WHERE (st.uid = ? COLLATE NOCASE OR s.seat_number = ? COLLATE NOCASE)
      AND b.booking_status = 'confirmed'
    """, (query.strip(), query.strip()))
    r = cursor.fetchone()
    conn.close()
    if r:
        return {
            "booking_id": r["booking_id"],
            "booking_date": r["booking_date"],
            "seat_number": r["seat_number"],
            "student_name": r["student_name"],
            "uid": r["uid"],
            "section": r["section"]
        }
    return None
