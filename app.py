import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from config import Config
import database
import ai_assistant

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config.from_object(Config)
CORS(app)

# Ensure database is initialized on startup
with app.app_context():
    database.init_db(seed_sample_bookings=True)

# ----------------------------------------------------
# Frontend Page Routes
# ----------------------------------------------------

@app.route("/")
def index():
    """Serves the main Campus Express student booking portal."""
    return render_template("index.html")

@app.route("/admin")
def admin():
    """Serves the authorized administrative dashboard."""
    return render_template("admin.html")

# ----------------------------------------------------
# REST API: Seats Management
# ----------------------------------------------------

@app.route("/api/seats", methods=["GET"])
def get_seats():
    """Retrieves all 66 bus seats with their live reservation statuses."""
    try:
        seats = database.get_all_seats()
        available_info = database.get_available_seats()
        return jsonify({
            "success": True,
            "total_seats": len(seats),
            "available_count": available_info["count"],
            "seats": seats
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/seats/<seat_number>", methods=["GET"])
def get_single_seat(seat_number):
    """Retrieves status of a specific seat."""
    try:
        seat = database.get_seat(seat_number)
        if not seat:
            return jsonify({"success": False, "error": f"Seat '{seat_number}' not found."}), 404
        return jsonify({"success": True, "seat": seat}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ----------------------------------------------------
# REST API: Student Verification
# ----------------------------------------------------

@app.route("/api/students/verify/<uid>", methods=["GET"])
def verify_student(uid):
    """Verifies student UID against authorized university visit roster."""
    try:
        student = database.get_student_by_uid(uid)
        if not student:
            return jsonify({
                "success": False,
                "message": f"UID '{uid}' is not on the authorized industrial visit roster."
            }), 404
        return jsonify({
            "success": True,
            "student": {
                "student_name": student["student_name"],
                "uid": student["uid"],
                "section": student["section"]
            }
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ----------------------------------------------------
# REST API: Bookings Management
# ----------------------------------------------------

@app.route("/api/bookings", methods=["GET"])
def get_bookings():
    """Retrieves all active passenger reservations for the admin manifest."""
    try:
        bookings = database.get_all_bookings(active_only=True)
        return jsonify({
            "success": True,
            "count": len(bookings),
            "bookings": bookings
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/bookings", methods=["POST"])
def create_reservation():
    """
    Creates a new bus reservation.
    Supports single reservation: { "seat_number": "1C", "uid": "24BAI70262", "email": "..." }
    Or batch reservations: { "bookings": [ { "seat_number": "1C", "uid": "..." }, ... ] }
    """
    try:
        data = request.get_json(force=True) or {}
        email = data.get("email", "").strip()

        # Handle batch or single booking
        entries = data.get("bookings")
        if not entries:
            # Single booking format
            seat_number = data.get("seat_number")
            uid = data.get("uid")
            if not seat_number or not uid:
                return jsonify({"success": False, "error": "Both 'seat_number' and 'uid' are required."}), 400
            entries = [{"seat_number": seat_number, "uid": uid}]

        created = []
        # Pre-validate unique UIDs within the batch submission
        uids_in_batch = set()
        seats_in_batch = set()
        for item in entries:
            u = item.get("uid", "").strip().upper()
            s = item.get("seat_number", "").strip().upper()
            if u in uids_in_batch:
                return jsonify({"success": False, "error": f"UID '{u}' appears multiple times in this submission."}), 400
            if s in seats_in_batch:
                return jsonify({"success": False, "error": f"Seat '{s}' appears multiple times in this submission."}), 400
            uids_in_batch.add(u)
            seats_in_batch.add(s)

        # Process each reservation atomically
        for item in entries:
            s_num = item.get("seat_number", "").strip().upper()
            s_uid = item.get("uid", "").strip().upper()
            success, msg, booking_obj = database.create_booking(s_num, s_uid, email)
            if not success:
                # If one fails, return detailed error
                return jsonify({"success": False, "error": msg}), 409
            created.append(booking_obj)

        return jsonify({
            "success": True,
            "message": f"Successfully confirmed {len(created)} seat reservation(s).",
            "bookings": created
        }), 201

    except Exception as e:
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500

@app.route("/api/bookings/<int:booking_id>", methods=["DELETE"])
def cancel_reservation(booking_id):
    """Cancels a confirmed reservation and frees the seat."""
    try:
        success, msg = database.cancel_booking(booking_id)
        if not success:
            return jsonify({"success": False, "error": msg}), 404
        return jsonify({"success": True, "message": msg}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/admin/reset", methods=["POST"])
def reset_bus_reservations():
    """Resets all bus bookings. Requires admin password."""
    try:
        data = request.get_json(silent=True) or {}
        password = data.get("password", "")
        if password != Config.ADMIN_PASSWORD:
            return jsonify({"success": False, "error": "Invalid administrator password. Access denied."}), 403

        success, msg, count = database.reset_all_bookings()
        if not success:
            return jsonify({"success": False, "error": msg}), 500
        return jsonify({
            "success": True,
            "message": msg,
            "reset_count": count
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/admin/summary", methods=["GET"])
def get_admin_summary():
    """Retrieves bus occupancy analytics and section breakdown."""
    try:
        summary = database.get_manifest_summary()
        return jsonify({"success": True, "summary": summary}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/admin/ai-summary", methods=["POST"])
def get_admin_ai_summary():
    """Generates an AI-driven operational summary of the bus manifest."""
    try:
        stats = database.get_manifest_summary()
        manifest = database.get_all_bookings(active_only=True)
        summary_text = ai_assistant.generate_admin_manifest_ai_summary(manifest, stats)
        return jsonify({
            "success": True,
            "ai_summary": summary_text,
            "stats": stats
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ----------------------------------------------------
# REST API: ExpressAI Assistant
# ----------------------------------------------------

@app.route("/api/ai/chat", methods=["POST"])
def ai_chat():
    """
    Communicates with ExpressAI.
    Accepts user message and recent conversation history.
    Returns AI response, tools executed, and source model.
    """
    try:
        data = request.get_json(force=True) or {}
        message = data.get("message", "").strip()
        history = data.get("history", [])

        if not message:
            return jsonify({"success": False, "error": "Message content is required."}), 400

        result = ai_assistant.chat_with_express_ai(message, history)
        return jsonify({
            "success": True,
            "response": result["response"],
            "tools_used": result.get("tools_used", []),
            "model": result.get("model", "ExpressAI"),
            "status": result.get("status", "success")
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"ExpressAI error: {str(e)}",
            "response": "I apologize, but I encountered an error processing your request. Please try again or check the bus map directly."
        }), 500


if __name__ == "__main__":
    print("=====================================================")
    print(" 🚍 Campus Express AI - Bus Reservation & Assistant ")
    print(" Microsoft AI-901 Certified Working Prototype")
    print("=====================================================")
    print(" Server running at: http://127.0.0.1:5000")
    print(" Admin Portal at:   http://127.0.0.1:5000/admin")
    print(" ExpressAI Chat at: http://127.0.0.1:5000/api/ai/chat")
    print("=====================================================")
    app.run(host="127.0.0.1", port=5000, debug=True)
