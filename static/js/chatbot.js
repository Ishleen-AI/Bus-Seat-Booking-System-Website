/**
 * Campus Express AI - ExpressAI Chatbot Interface
 * Connects to Microsoft Foundry / ExpressAI REST API with tool-calling transparency.
 */

let chatHistory = [];
let isWaitingForAi = false;

// Quick suggested prompt options
const SUGGESTED_PROMPTS = [
    "How many seats are available?",
    "How do I book a bus seat?",
    "Is seat 1A available?",
    "Can I book more than one seat?",
    "What are the cancellation rules?"
];

// Toggle chatbot drawer visibility
function toggleChatbot() {
    const chatWindow = document.getElementById("express-ai-window");
    const badge = document.getElementById("ai-unread-badge");
    if (!chatWindow) return;

    if (chatWindow.classList.contains("hidden")) {
        chatWindow.classList.remove("hidden");
        chatWindow.classList.add("flex");
        if (badge) badge.classList.add("hidden");
        scrollToBottom();
        const input = document.getElementById("ai-user-input");
        if (input) input.focus();
    } else {
        chatWindow.classList.remove("flex");
        chatWindow.classList.add("hidden");
    }
}

// Render initial greeting message if empty
function initChatbot() {
    const messagesContainer = document.getElementById("ai-messages-container");
    if (!messagesContainer) return;

    if (chatHistory.length === 0) {
        appendAssistantMessage(
            "Hello! I am **ExpressAI**, your virtual reservation assistant for Campus Express. 🚌\n\n" +
            "I'm integrated with Microsoft Foundry and can check live bus seat availability, guide your reservation, and explain campus booking policies.\n\n" +
            "How can I assist you today?",
            [],
            "ExpressAI Initializer"
        );
    }
    renderSuggestions();
}

// Render clickable quick prompt chips
function renderSuggestions() {
    const container = document.getElementById("ai-suggestions-container");
    if (!container) return;

    container.innerHTML = SUGGESTED_PROMPTS.map(p => `
        <button onclick="sendQuickPrompt('${p.replace(/'/g, "\\'")}')" 
                class="text-xs bg-slate-100 hover:bg-rose-50 hover:text-rose-600 text-slate-700 font-medium px-2.5 py-1 rounded-full border border-slate-200 transition shrink-0 whitespace-nowrap">
            ${p}
        </button>
    `).join("");
}

function sendQuickPrompt(promptText) {
    const input = document.getElementById("ai-user-input");
    if (input) {
        input.value = promptText;
        sendUserMessage();
    }
}

// Send user message to /api/ai/chat
async function sendUserMessage() {
    const input = document.getElementById("ai-user-input");
    if (!input || isWaitingForAi) return;

    const message = input.value.trim();
    if (!message) return;

    // Append to UI
    appendUserMessage(message);
    chatHistory.push({ role: "user", content: message });
    input.value = "";

    // Show typing indicator
    showTypingIndicator();
    isWaitingForAi = true;

    try {
        const response = await fetch("/api/ai/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: message,
                history: chatHistory.slice(-8)
            })
        });

        const data = await response.json();
        hideTypingIndicator();

        if (response.ok && data.success) {
            const aiText = data.response;
            const toolsUsed = data.tools_used || [];
            const modelUsed = data.model || "Microsoft Foundry";

            appendAssistantMessage(aiText, toolsUsed, modelUsed);
            chatHistory.push({ role: "assistant", content: aiText });
        } else {
            appendAssistantMessage(
                "I apologize, but I could not reach the AI service right now. Please check your internet connection or use the interactive bus map directly.",
                [],
                "System Error"
            );
        }
    } catch (err) {
        console.error("ExpressAI fetch error:", err);
        hideTypingIndicator();
        appendAssistantMessage(
            "An error occurred while connecting to ExpressAI backend. Please try again.",
            [],
            "Network Exception"
        );
    } finally {
        isWaitingForAi = false;
        scrollToBottom();
    }
}

// DOM Append User Message
function appendUserMessage(text) {
    const container = document.getElementById("ai-messages-container");
    if (!container) return;

    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const div = document.createElement("div");
    div.className = "flex justify-end chatbot-bubble-enter mb-3";
    div.innerHTML = `
        <div class="max-w-[85%] bg-rose-500 text-white rounded-2xl rounded-tr-sm px-4 py-2.5 shadow-sm">
            <p class="text-sm font-normal break-words">${escapeHtml(text)}</p>
            <span class="block text-[10px] text-rose-100 text-right mt-1 opacity-80">${time}</span>
        </div>
    `;
    container.appendChild(div);
    scrollToBottom();
}

// DOM Append Assistant Message with Markdown Support & Tool Badges
function appendAssistantMessage(rawText, toolsUsed = [], model = "ExpressAI") {
    const container = document.getElementById("ai-messages-container");
    if (!container) return;

    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const formattedHtml = formatMarkdown(rawText);

    // Format tool usage badges if tools were invoked
    let toolsMarkup = "";
    if (toolsUsed && toolsUsed.length > 0) {
        const toolNames = toolsUsed.map(t => typeof t === "string" ? t : (t.tool || "database_tool")).join(", ");
        toolsMarkup = `
            <div class="mt-2.5 pt-2 border-t border-slate-100 flex items-center gap-1.5 text-[11px] text-emerald-700 font-medium">
                <i class="fa-solid fa-bolt-lightning text-emerald-500"></i>
                <span>Grounded via backend: <code>${escapeHtml(toolNames)}</code></span>
            </div>
        `;
    }

    const div = document.createElement("div");
    div.className = "flex items-start gap-2.5 chatbot-bubble-enter mb-3";
    div.innerHTML = `
        <div class="w-8 h-8 rounded-full bg-slate-900 text-rose-400 flex items-center justify-center shrink-0 shadow-sm border border-slate-700 mt-1">
            <i class="fa-solid fa-robot text-sm"></i>
        </div>
        <div class="max-w-[85%] bg-white border border-slate-200 text-slate-800 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
            <div class="text-sm leading-relaxed prose prose-sm">${formattedHtml}</div>
            ${toolsMarkup}
            <div class="flex justify-between items-center mt-2 pt-1.5 border-t border-slate-100 text-[10px] text-slate-400">
                <span class="flex items-center gap-1 font-mono"><i class="fa-brands fa-microsoft text-blue-500"></i> ${escapeHtml(model)}</span>
                <span>${time}</span>
            </div>
        </div>
    `;
    container.appendChild(div);
    scrollToBottom();
}

// Simple Markdown Formatter for bold, bullets, links, code
function formatMarkdown(text) {
    if (!text) return "";
    let html = escapeHtml(text);

    // Bold **text**
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Italic *text*
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    // Code `code`
    html = html.replace(/`(.*?)`/g, '<code class="bg-slate-100 text-rose-600 px-1 py-0.5 rounded text-xs">$1</code>');
    // Bullet lines starting with • or -
    html = html.replace(/^[•\-]\s+(.*)$/gm, '<li class="ml-4 list-disc">$1</li>');
    // Line breaks
    html = html.replace(/\n\n/g, '<br><br>').replace(/\n/g, '<br>');

    return html;
}

function showTypingIndicator() {
    const container = document.getElementById("ai-messages-container");
    if (!container) return;

    const existing = document.getElementById("ai-typing-indicator");
    if (existing) return;

    const div = document.createElement("div");
    div.id = "ai-typing-indicator";
    div.className = "flex items-start gap-2.5 mb-3 chatbot-bubble-enter";
    div.innerHTML = `
        <div class="w-8 h-8 rounded-full bg-slate-900 text-rose-400 flex items-center justify-center shrink-0 shadow-sm border border-slate-700">
            <i class="fa-solid fa-robot text-sm"></i>
        </div>
        <div class="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm flex items-center gap-1.5">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="text-xs text-slate-400 ml-2 font-medium">ExpressAI is thinking...</span>
        </div>
    `;
    container.appendChild(div);
    scrollToBottom();
}

function hideTypingIndicator() {
    const el = document.getElementById("ai-typing-indicator");
    if (el) el.remove();
}

function scrollToBottom() {
    const container = document.getElementById("ai-messages-container");
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}

function escapeHtml(str) {
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function clearChat() {
    chatHistory = [];
    const container = document.getElementById("ai-messages-container");
    if (container) container.innerHTML = "";
    initChatbot();
}

// Global functions
window.toggleChatbot = toggleChatbot;
window.sendUserMessage = sendUserMessage;
window.sendQuickPrompt = sendQuickPrompt;
window.clearChat = clearChat;

// Initialize on load
document.addEventListener("DOMContentLoaded", () => {
    initChatbot();

    const input = document.getElementById("ai-user-input");
    if (input) {
        input.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendUserMessage();
            }
        });
    }
});
