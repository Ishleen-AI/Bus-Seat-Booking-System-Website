/**
 * Campus Express AI - Admin Dashboard Management
 * Connects to SQLite backend for live passenger manifest, occupancy statistics, and AI summaries.
 */

let currentBookings = [];
let currentSummary = {};
let manifestRefreshInterval;

function showAdminDashboard() {
    document.getElementById("admin-login").classList.add("hidden");
    document.getElementById("admin-dashboard").classList.remove("hidden");
    document.getElementById("admin-dashboard").classList.add("flex");
    document.getElementById("admin-logout-btn").classList.remove("hidden");
    loadManifest();
    if (!manifestRefreshInterval) {
        manifestRefreshInterval = setInterval(loadManifest, 10000);
    }
}

function showAdminLogin() {
    document.getElementById("admin-dashboard").classList.add("hidden");
    document.getElementById("admin-dashboard").classList.remove("flex");
    document.getElementById("admin-login").classList.remove("hidden");
    document.getElementById("admin-logout-btn").classList.add("hidden");
    if (manifestRefreshInterval) {
        clearInterval(manifestRefreshInterval);
        manifestRefreshInterval = null;
    }
}

async function loginAdmin(event) {
    event.preventDefault();
    const passwordInput = document.getElementById("admin-password");
    const error = document.getElementById("admin-login-error");
    try {
        const response = await fetch("/api/admin/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ password: passwordInput.value })
        });
        const data = await response.json();

        if (!response.ok || !data.success) {
            error.textContent = data.error || "Sign-in failed.";
            error.classList.remove("hidden");
            passwordInput.select();
            return;
        }

        passwordInput.value = "";
        error.classList.add("hidden");
        showAdminDashboard();
    } catch (err) {
        console.error("Administrator sign-in failed:", err);
        error.textContent = "Unable to contact the server. Please try again.";
        error.classList.remove("hidden");
    }
}

async function logoutAdmin() {
    try {
        const response = await fetch("/api/admin/logout", { method: "POST" });
        if (!response.ok) {
            console.error("Administrator sign-out failed.");
        }
    } finally {
        showAdminLogin();
    }
}

// Load live manifest data and occupancy stats from Flask backend
async function loadManifest() {
    const tbody = document.getElementById("admin-table-body");
    const refreshBtn = document.getElementById("refresh-btn");
    if (refreshBtn) refreshBtn.classList.add("animate-spin");

    try {
        // Fetch bookings manifest
        const resBookings = await fetch("/api/bookings");
        if (resBookings.status === 401) {
            showAdminLogin();
            return;
        }
        const dataBookings = await resBookings.json();

        // Fetch occupancy summary
        const resSummary = await fetch("/api/admin/summary");
        if (resSummary.status === 401) {
            showAdminLogin();
            return;
        }
        const dataSummary = await resSummary.json();

        if (dataSummary.success && dataSummary.summary) {
            currentSummary = dataSummary.summary;
            updateStatCards(currentSummary);
        }

        if (dataBookings.success && dataBookings.bookings) {
            currentBookings = dataBookings.bookings;
            renderManifestTable(currentBookings);
        }
    } catch (err) {
        console.error("Failed to load admin manifest:", err);
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="7" class="p-6 text-center text-rose-500 font-semibold">Failed to connect to backend server. Make sure Flask is running.</td></tr>`;
        }
    } finally {
        if (refreshBtn) refreshBtn.classList.remove("animate-spin");
    }
}

// Update Top Statistics Cards
function updateStatCards(s) {
    const totalEl = document.getElementById("stat-total-seats");
    const occEl = document.getElementById("stat-occupied-seats");
    const availEl = document.getElementById("stat-available-seats");
    const rateEl = document.getElementById("stat-occupancy-rate");
    const cancelEl = document.getElementById("stat-cancelled-count");

    if (totalEl) totalEl.innerText = s.total_seats || 66;
    if (occEl) occEl.innerText = s.occupied_seats || 0;
    if (availEl) availEl.innerText = s.available_seats || 0;
    if (rateEl) rateEl.innerText = `${s.occupancy_rate || 0}%`;
    if (cancelEl) cancelEl.innerText = s.cancelled_count || 0;
}

// Render Manifest Table Rows
function renderManifestTable(bookings) {
    const tbody = document.getElementById("admin-table-body");
    if (!tbody) return;

    if (!bookings || bookings.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="p-8 text-center text-slate-400">No active seat reservations recorded in the database.</td></tr>`;
        return;
    }

    let rows = "";
    bookings.forEach(b => {
        rows += `
            <tr class="hover:bg-slate-50 transition border-b border-slate-100">
                <td class="p-4 font-bold text-slate-900 flex items-center gap-2">
                    <span class="w-7 h-7 rounded-lg bg-slate-100 text-slate-700 flex items-center justify-center font-mono text-xs border border-slate-200">${b.seat_number}</span>
                </td>
                <td class="p-4 text-slate-800 capitalize font-medium">${escapeHtml(b.student_name)}</td>
                <td class="p-4 text-emerald-600 font-mono font-bold bg-emerald-50/50">${escapeHtml(b.uid)}</td>
                <td class="p-4 text-slate-600">${escapeHtml(b.section || "—")}</td>
                <td class="p-4 text-slate-600 font-mono text-xs">${escapeHtml(b.phone || "—")}</td>
                <td class="p-4 text-blue-600 text-xs font-medium bg-blue-50/40">${escapeHtml(b.entry_email || "portal")}</td>
                <td class="p-4 text-right">
                    <button onclick="cancelBooking(${b.booking_id}, '${b.seat_number}', '${escapeHtml(b.student_name)}')" 
                            class="px-2.5 py-1 text-xs bg-rose-50 hover:bg-rose-100 text-rose-700 font-semibold rounded-lg border border-rose-200 transition flex items-center gap-1.5 ml-auto">
                        <i class="fa-solid fa-ban"></i> Cancel
                    </button>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = rows;
}

// Cancel a reservation
async function cancelBooking(bookingId, seatNumber, studentName) {
    if (!confirm(`Are you sure you want to cancel the reservation for Seat ${seatNumber} (${studentName})? The seat will immediately become available for other students.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/bookings/${bookingId}`, {
            method: "DELETE"
        });
        const data = await response.json();

        if (response.ok && data.success) {
            alert(`✅ ${data.message}`);
            await loadManifest();
        } else {
            alert(`❌ Error: ${data.error || "Failed to cancel reservation."}`);
        }
    } catch (err) {
        console.error("Cancel booking error:", err);
        alert("Failed to communicate with the server.");
    }
}

// Reset Entire Bus Manifest
async function resetBus() {
    if (!confirm("⚠️ This will cancel all confirmed bookings and free all 66 seats. Continue?")) return;

    try {
        const response = await fetch("/api/admin/reset", {
            method: "POST",
        });
        const data = await response.json();

        if (response.ok && data.success) {
            alert(`✅ Bus Reset Successful: ${data.message}`);
            await loadManifest();
        } else {
            alert(`❌ ${data.error || "Access Denied."}`);
        }
    } catch (err) {
        console.error("Reset error:", err);
        alert("Server error during bus reset.");
    }
}

// Generate AI Manifest Summary for Coordinators
async function generateAiSummary() {
    const summaryCard = document.getElementById("ai-summary-card");
    const summaryContent = document.getElementById("ai-summary-content");
    const aiBtn = document.getElementById("generate-ai-btn");

    if (!summaryCard || !summaryContent) return;

    summaryCard.classList.remove("hidden");
    summaryContent.innerHTML = `
        <div class="flex items-center gap-3 text-slate-500 py-3">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="text-sm">ExpressAI is analyzing passenger distribution and calculating capacity metrics...</span>
        </div>
    `;

    if (aiBtn) aiBtn.disabled = true;

    try {
        const res = await fetch("/api/admin/ai-summary", {
            method: "POST"
        });
        const data = await res.json();

        if (res.ok && data.success) {
            summaryContent.innerHTML = `
                <div class="text-sm text-slate-700 leading-relaxed space-y-2">
                    ${formatAiMarkdown(data.ai_summary)}
                </div>
            `;
        } else {
            summaryContent.innerHTML = `<p class="text-sm text-rose-500">Failed to generate summary: ${data.error || "Unknown error"}</p>`;
        }
    } catch (e) {
        console.error("AI Summary error:", e);
        summaryContent.innerHTML = `<p class="text-sm text-rose-500">Network error while connecting to ExpressAI.</p>`;
    } finally {
        if (aiBtn) aiBtn.disabled = false;
    }
}

function formatAiMarkdown(text) {
    if (!text) return "";
    let html = escapeHtml(text);
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    html = html.replace(/^[•\-]\s+(.*)$/gm, '<li class="ml-4 list-disc">$1</li>');
    html = html.replace(/\n\n/g, '<br><br>').replace(/\n/g, '<br>');
    return html;
}

function escapeHtml(str) {
    return String(str || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Global functions for inline HTML event handlers
window.loadManifest = loadManifest;
window.cancelBooking = cancelBooking;
window.resetBus = resetBus;
window.generateAiSummary = generateAiSummary;
window.logoutAdmin = logoutAdmin;

// Initial load
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("admin-login-form").addEventListener("submit", loginAdmin);
    fetch("/api/admin/session")
        .then(response => response.json())
        .then(data => data.authenticated ? showAdminDashboard() : showAdminLogin())
        .catch(() => showAdminLogin());
});
