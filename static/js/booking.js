/**
 * Campus Express AI - Bus Booking Logic
 * Manages 66-seat bus interactive layout, selection, UID validation, and transactional API bookings.
 */

let seatsData = {};
let selectedSeats = [];
let loggedInEmail = sessionStorage.getItem("campus_express_email") || "";

// Fetch all 66 seats from Flask REST API
async function fetchSeats() {
    try {
        const response = await fetch("/api/seats");
        const data = await response.json();
        if (data.success && data.seats) {
            seatsData = {};
            data.seats.forEach(s => {
                seatsData[s.seat_number] = s;
            });
            renderBus();
        }
    } catch (error) {
        console.error("Error fetching seats from backend:", error);
    }
}

// Render the 66-seat bus layout: Rows 1-12 (A-E) + Back Row 13 (A-F)
function renderBus() {
    const grid = document.getElementById("bus-grid");
    if (!grid) return;

    let html = "";
    // Rows 1 to 12: 5 seats each (A, B on left, C, D, E on right)
    for (let r = 1; r <= 12; r++) {
        html += `
        <div class="flex justify-between items-center group relative">
            <div class="flex gap-2 sm:gap-3">
                ${renderSeatMarkup(`${r}A`)}
                ${renderSeatMarkup(`${r}B`)}
            </div>
            <div class="w-8 sm:w-10 text-center text-slate-300 font-black text-sm select-none">${r}</div>
            <div class="flex gap-2 sm:gap-3">
                ${renderSeatMarkup(`${r}C`)}
                ${renderSeatMarkup(`${r}D`)}
                ${renderSeatMarkup(`${r}E`)}
            </div>
        </div>
        `;
    }

    // Back Row (Row 13): 6 seats (A, B, C, D, E, F)
    html += `
    <div class="mt-8 pt-6 border-t border-slate-200 flex justify-between gap-1 relative">
        <div class="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-white px-2 text-xs font-bold text-slate-400 select-none">
            Back Row (Row 13)
        </div>
        ${['A','B','C','D','E','F'].map(c => renderSeatMarkup(`13${c}`)).join('')}
    </div>
    `;

    grid.innerHTML = html;
    updateCart();
}

// Helper to generate seat DOM markup
function renderSeatMarkup(id) {
    const s = seatsData[id] || { booked: false, student_name: "" };
    const isSel = selectedSeats.includes(id);

    let cls = "seat relative w-10 h-11 sm:w-12 sm:h-14 rounded-t-xl rounded-b-md border-2 flex flex-col items-center justify-center text-xs sm:text-sm font-bold select-none cursor-pointer overflow-hidden ";
    let title = `Seat ${id}`;
    let cushion = "bg-emerald-100";
    let content = `<span class="z-10 mb-1.5">${id}</span>`;

    if (s.booked) {
        cls += "bg-slate-200 border-slate-300 text-slate-500 cursor-not-allowed";
        title = `Booked by ${s.student_name || "Reserved Passenger"}`;
        cushion = "bg-slate-300";

        const firstName = (s.student_name || "Booked").split(" ")[0];
        content = `
            <span class="z-10 text-[9px] sm:text-[10px] leading-none mt-1 sm:mt-0 opacity-70">${id}</span>
            <span class="z-10 text-[8px] sm:text-[9px] font-bold leading-tight truncate w-full text-center px-0.5 mb-1.5 text-slate-700 capitalize">${firstName}</span>
        `;
    } else if (isSel) {
        cls += "bg-rose-500 border-rose-600 text-white animate-pop shadow-md shadow-rose-200";
        cushion = "bg-rose-600";
    } else {
        cls += "bg-white border-emerald-500 text-slate-600 hover:bg-emerald-50";
    }

    return `
        <div class="${cls}" onclick="toggleSeat('${id}')" title="${title}">
            <div class="absolute bottom-1 w-[70%] h-2 sm:h-2.5 rounded-[3px] ${cushion}"></div>
            ${content}
        </div>
    `;
}

// Toggle seat selection
function toggleSeat(id) {
    const s = seatsData[id];
    if (s && s.booked) {
        alert(`Seat ${id} is already reserved by ${s.student_name || "another passenger"}.`);
        return;
    }
    const idx = selectedSeats.indexOf(id);
    if (idx > -1) {
        selectedSeats.splice(idx, 1);
    } else {
        selectedSeats.push(id);
    }
    renderBus();
}

// Update the right summary cart
function updateCart() {
    const empty = document.getElementById("cart-empty");
    const active = document.getElementById("cart-active");
    const list = document.getElementById("selected-list");

    if (!empty || !active || !list) return;

    if (selectedSeats.length === 0) {
        empty.classList.remove("hidden");
        active.classList.add("hidden");
        active.classList.remove("flex");
    } else {
        empty.classList.add("hidden");
        active.classList.remove("hidden");
        active.classList.add("flex");
        list.innerHTML = selectedSeats.map(id => `
            <div class="bg-rose-50 border border-rose-200 text-rose-700 px-3 py-1.5 rounded-lg text-sm font-bold flex items-center gap-2 animate-pop">
                ${id} <i class="fa-solid fa-xmark text-xs cursor-pointer hover:text-rose-900" onclick="toggleSeat('${id}')"></i>
            </div>
        `).join("");
    }
}

// UID Verification against Backend API
async function checkUID(seatId) {
    const uidInput = document.getElementById(`uid-${seatId}`);
    const nameInput = document.getElementById(`name-${seatId}`);
    const statusIcon = document.getElementById(`status-${seatId}`);
    if (!uidInput || !nameInput || !statusIcon) return;

    const enteredUID = uidInput.value.trim().toUpperCase();
    if (enteredUID.length < 1) {
        nameInput.value = "";
        statusIcon.innerHTML = "";
        uidInput.classList.remove("border-emerald-500", "bg-emerald-50", "border-rose-500");
        uidInput.classList.add("border-slate-300");
        return;
    }

    try {
        const res = await fetch(`/api/students/verify/${encodeURIComponent(enteredUID)}`);
        const data = await res.json();

        if (data.success && data.student) {
            nameInput.value = data.student.student_name;
            uidInput.classList.remove("border-slate-300", "border-rose-500");
            uidInput.classList.add("border-emerald-500", "bg-emerald-50");
            statusIcon.innerHTML = `<i class="fa-solid fa-circle-check text-emerald-500" title="Authorized: ${data.student.student_name} (${data.student.section})"></i>`;
        } else {
            nameInput.value = "";
            statusIcon.innerHTML = "";
            uidInput.classList.remove("border-emerald-500", "bg-emerald-50");
            if (enteredUID.length > 5) {
                uidInput.classList.add("border-rose-500");
            } else {
                uidInput.classList.add("border-slate-300");
                uidInput.classList.remove("border-rose-500");
            }
        }
    } catch (e) {
        console.error("UID check error:", e);
    }
}

// Open booking modal for passenger verification
function openBookingModal() {
    if (selectedSeats.length === 0) return;
    const errorDiv = document.getElementById("error-message");
    if (errorDiv) errorDiv.classList.add("hidden");

    const body = document.getElementById("modal-body");
    body.innerHTML = selectedSeats.map(id => `
        <div class="p-4 border border-slate-200 rounded-xl bg-white shadow-sm relative overflow-hidden">
            <div class="absolute top-0 left-0 w-1 h-full bg-rose-500"></div>
            <div class="flex justify-between items-center mb-3">
                <p class="font-bold text-slate-800 flex items-center gap-2">
                    <i class="fa-solid fa-couch text-rose-500"></i> Seat ${id}
                </p>
                <span id="status-${id}"></span>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                    <label class="block text-xs font-semibold text-slate-500 mb-1">UNIVERSITY UID</label>
                    <input type="text" id="uid-${id}" onkeyup="checkUID('${id}')" placeholder="e.g. DEMO0001" class="w-full p-2.5 border border-slate-300 rounded-lg text-sm outline-none transition uppercase">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-500 mb-1">STUDENT NAME (AUTO-FILLED)</label>
                    <input type="text" id="name-${id}" readonly placeholder="Type UID to verify name" class="w-full p-2.5 bg-slate-100 border border-slate-200 text-slate-600 font-medium rounded-lg text-sm outline-none cursor-not-allowed">
                </div>
            </div>
        </div>
    `).join("");

    const modal = document.getElementById("modal");
    modal.classList.remove("hidden");
    modal.classList.add("flex");
}

function closeModal() {
    const modal = document.getElementById("modal");
    modal.classList.remove("flex");
    modal.classList.add("hidden");
}

function showError(msg) {
    const errDiv = document.getElementById("error-message");
    if (errDiv) {
        errDiv.innerText = msg;
        errDiv.classList.remove("hidden");
    }
}

// Commit reservation transaction to Flask REST API
async function processFinalBooking() {
    const entries = [];
    const tempUIDs = new Set();

    for (const id of selectedSeats) {
        const uidInput = document.getElementById(`uid-${id}`);
        const nameInput = document.getElementById(`name-${id}`);
        const uid = uidInput ? uidInput.value.trim().toUpperCase() : "";

        if (!uid) return showError(`Please enter a valid UID for Seat ${id}.`);
        if (!nameInput || !nameInput.value) return showError(`UID "${uid}" is not authorized or verified.`);
        if (tempUIDs.has(uid)) return showError(`UID "${uid}" is entered multiple times in this form.`);
        tempUIDs.add(uid);

        entries.push({ seat_number: id, uid: uid });
    }

    try {
        const response = await fetch("/api/bookings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                email: loggedInEmail || "guest@university.edu",
                bookings: entries
            })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            selectedSeats = [];
            closeModal();
            await fetchSeats();
            alert("🎉 Booking Confirmed Successfully! Your reservation is recorded in the central database.");
        } else {
            showError(data.error || "Reservation failed. Please verify your details.");
        }
    } catch (err) {
        console.error("Booking error:", err);
        showError("Network or database communication failure. Please try again.");
    }
}

// Access portal modal logic
function grantAccess() {
    const emailInput = document.getElementById("access-email");
    const emailVal = emailInput ? emailInput.value.trim() : "";
    if (!emailVal || !emailVal.includes("@")) {
        alert("Please enter a valid university email address to enter the portal.");
        return;
    }
    loggedInEmail = emailVal;
    sessionStorage.setItem("campus_express_email", loggedInEmail);
    applyLoggedInState();
}

function applyLoggedInState() {
    const loginModal = document.getElementById("login-modal");
    const bodyContainer = document.getElementById("body-container");
    const userDisplay = document.getElementById("user-display");
    const userEmail = document.getElementById("current-user-email");

    if (loginModal) loginModal.classList.add("hidden");
    if (bodyContainer) bodyContainer.classList.remove("overflow-hidden");
    if (userEmail) userEmail.innerText = loggedInEmail;
    if (userDisplay) {
        userDisplay.classList.remove("hidden");
        userDisplay.classList.add("flex");
    }
}

// Expose globals for HTML event handlers
window.toggleSeat = toggleSeat;
window.checkUID = checkUID;
window.openBookingModal = openBookingModal;
window.closeModal = closeModal;
window.processFinalBooking = processFinalBooking;
window.grantAccess = grantAccess;

// Initialization on DOM Ready
document.addEventListener("DOMContentLoaded", () => {
    if (loggedInEmail) {
        applyLoggedInState();
    }
    fetchSeats();
    // Poll every 8 seconds for real-time sync with other users/admin
    setInterval(fetchSeats, 8000);
});
