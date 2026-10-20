// 1. SETUP VARIABLES
const username = localStorage.getItem("current_user") || "Guest";
document.getElementById("display-username").innerText = username;

// Generate a random ID for the current session
let currentSessionId = generateUUID();

// 2. ON LOAD: Fetch History
window.onload = function() {
    loadSidebarHistory();
};

// --- CORE FUNCTIONS ---

async function sendMessage() {
    const inputField = document.getElementById("user-input");
    const userMessage = inputField.value.trim();
    if (!userMessage) return;

    // Add User Message to UI
    addMessageToUI(userMessage, "user");
    inputField.value = ""; 

    // Add Loading Bubble
    const loadingId = addMessageToUI("Typing...", "bot", true);

    try {
        // --- THIS IS THE PART THAT WAS WRONG ---
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                message: userMessage,         // Field 1
                username: username,           // Field 2 (MUST BE HERE)
                session_id: currentSessionId  // Field 3 (MUST BE HERE)
            })
        });
        // ---------------------------------------

        const data = await response.json();

        if (!response.ok) {
            console.error("Server Error Details:", data);
            throw new Error(data.detail || "Server rejected request");
        }
        
        removeMessage(loadingId);
        if (data.reply) {
            addMessageToUI(data.reply, "bot");
        } else {
            addMessageToUI("Error: Bot reply is missing.", "bot");
        }

        loadSidebarHistory();

    } catch (error) {
        removeMessage(loadingId);
        addMessageToUI("System Error. Check Console.", "bot");
        console.error("Full Error:", error);
    }
}
// --- SIDEBAR HISTORY LOGIC ---

async function loadSidebarHistory() {
    try {
        const response = await fetch("/api/get_history", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: username })
        });
        const data = await response.json();
        
        const historyContainer = document.getElementById("history-container");
        // Keep the title, clear the items
        historyContainer.innerHTML = '<p class="history-title">Your History</p>';

        data.history.forEach(chat => {
            const div = document.createElement("div");
            div.className = "history-item";
            div.innerText = chat.title;
            div.onclick = () => loadOldChat(chat.session_id); // Make it clickable
            historyContainer.appendChild(div);
        });

    } catch (e) { console.error("History error", e); }
}

// CLICK "New Chat"
function startNewChat() {
    currentSessionId = generateUUID(); // Generate new ID
    const chatBox = document.getElementById("chat-box");
    chatBox.innerHTML = ''; // Clear Screen
    
    // Add Welcome Message
    addMessageToUI("New session bro! What's the plan?", "bot");
}

// CLICK History Item
async function loadOldChat(sessionId) {
    currentSessionId = sessionId;
    const chatBox = document.getElementById("chat-box");
    chatBox.innerHTML = ''; // Clear Screen
    
    const response = await fetch("/api/load_chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId })
    });
    const data = await response.json();

    data.messages.forEach(msg => {
        addMessageToUI(msg.text, msg.sender);
    });
}

// --- HELPERS ---

function addMessageToUI(text, sender, isLoading = false) {
    const chatBox = document.getElementById("chat-box");
    const msgDiv = document.createElement("div");
    msgDiv.classList.add("message", sender);
    if (isLoading) msgDiv.id = "loading-bubble";

    const icon = sender === "bot" ? '<i class="fas fa-robot"></i>' : '<i class="fas fa-user"></i>';
    msgDiv.innerHTML = `<div class="avatar">${icon}</div><div class="text">${text}</div>`;
    
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
    return msgDiv.id;
}

function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function generateUUID() { // Simple ID generator
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Event Listener for Enter key
document.getElementById("user-input").addEventListener("keypress", function(e) {
    if (e.key === "Enter") sendMessage();
});