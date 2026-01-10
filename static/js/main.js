/*
 * NeuralQuery - Main JavaScript
 * Handles all frontend logic for the chat interface
 */

// API Base URL
const API_BASE = window.location.origin;

// Global State
let currentConversationId = null;
let currentUser = null;
let conversations = [];

// =============================================================================
// AUTHENTICATION & INITIALIZATION
// =============================================================================

// Check if user is authenticated
function checkAuth() {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');
    const path = window.location.pathname;

    // If on auth pages (login/register), do not redirect if no token
    if (path === '/login' || path === '/register') {
        // If already logged in, redirect to chat
        if (token && user) {
            window.location.replace('/chat');
        }
        return false; // Stop checking
    }

    if (!token || !user) {
        // Only redirect if not already on login page
        if (path !== '/login' && path !== '/register') {
            window.location.href = '/login';
        }
        return false;
    }

    try {
        currentUser = JSON.parse(user);
        updateUserInfo();
        return true;
    } catch (e) {
        console.error('Failed to parse user data:', e);
        logout();
        return false;
    }
}

// Update user info in sidebar
function updateUserInfo() {
    if (currentUser) {
        const nameEl = document.getElementById('userName');
        const emailEl = document.getElementById('userEmail');
        const avatarEl = document.getElementById('userAvatar');

        if (nameEl) nameEl.textContent = currentUser.full_name || 'User';
        if (emailEl) emailEl.textContent = currentUser.email || '';

        if (avatarEl && currentUser.full_name) {
            const initials = currentUser.full_name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
            avatarEl.textContent = initials;
        }
    }
}

// Logout
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
}

// =============================================================================
// API CALLS
// =============================================================================

// Generic API call function
async function apiCall(endpoint, options = {}) {
    const token = localStorage.getItem('token');

    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        }
    };

    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    });

    const data = await response.json();

    if (response.status === 401) {
        logout();
        throw new Error('Unauthorized');
    }

    return data;
}

// Get all conversations
async function loadConversations() {
    try {
        const data = await apiCall('/api/conversations');

        if (data.success) {
            conversations = data.conversations;
            renderConversations();
        }
    } catch (error) {
        console.error('Error loading conversations:', error);
    }
}

// Get specific conversation
async function loadConversation(id) {
    try {
        const data = await apiCall(`/api/conversations/${id}`);

        if (data.success) {
            currentConversationId = id;
            renderMessages(data.conversation.messages);
            updateActiveConversation(id);
        }
    } catch (error) {
        console.error('Error loading conversation:', error);
    }
}

// Send research query
async function sendQuery(query) {
    showLoading(true);
    hideWelcomeMessage();

    // Add user message to UI immediately
    addMessage('user', query);

    // Show typing indicator
    showTypingIndicator();

    try {
        const data = await apiCall('/api/research', {
            method: 'POST',
            body: JSON.stringify({
                query,
                conversation_id: currentConversationId
            })
        });

        hideTypingIndicator();

        if (data.success) {
            currentConversationId = data.conversation_id;

            // Add assistant response
            addMessage('assistant', data.response, {
                accuracy: data.accuracy,
                sources: data.sources
            });

            // Reload conversations to update sidebar
            loadConversations();
        } else {
            addMessage('assistant', `Error: ${data.error || 'Research failed'}`);
        }
    } catch (error) {
        hideTypingIndicator();
        console.error('Error sending query:', error);
        addMessage('assistant', 'An error occurred. Please try again.');
    } finally {
        showLoading(false);
    }
}

// Delete conversation
async function deleteConversation(id) {
    if (!confirm('Delete this conversation?')) return;

    try {
        const data = await apiCall(`/api/conversations/${id}`, {
            method: 'DELETE'
        });

        if (data.success) {
            if (currentConversationId === id) {
                startNewChat();
            }
            loadConversations();
        }
    } catch (error) {
        console.error('Error deleting conversation:', error);
    }
}

// =============================================================================
// UI RENDERING
// =============================================================================

// Render conversations list
function renderConversations() {
    const listEl = document.getElementById('conversationList');

    if (conversations.length === 0) {
        listEl.innerHTML = `
            <div class="loading-conversations">
                <p>No conversations yet.<br>Start a new chat!</p>
            </div>
        `;
        return;
    }

    listEl.innerHTML = conversations.map(conv => `
        <div class="conversation-item ${conv.id === currentConversationId ? 'active' : ''}" 
             onclick="loadConversation(${conv.id})">
            <div class="conversation-title">${escapeHtml(conv.title || 'Untitled')}</div>
            <div class="conversation-meta">
                <span>${formatDate(conv.updated_at)}</span>
                <button class="conversation-delete" onclick="event.stopPropagation(); deleteConversation(${conv.id})" title="Delete">
                    🗑️
                </button>
            </div>
        </div>
    `).join('');
}

// Render messages
function renderMessages(messages) {
    const messagesEl = document.getElementById('chatMessages');
    messagesEl.innerHTML = '';

    messages.forEach(msg => {
        addMessage(msg.role, msg.content, {
            accuracy: msg.accuracy_score ? {
                overall_accuracy: msg.accuracy_score,
                sources_analyzed: msg.sources_count
            } : null,
            skipScroll: true
        });
    });

    scrollToBottom();
}

// Add a message to the chat
function addMessage(role, content, options = {}) {
    const messagesEl = document.getElementById('chatMessages');
    const messageEl = document.createElement('div');
    messageEl.className = `message ${role}`;

    let metaHtml = '';

    if (role === 'assistant' && options.accuracy) {
        const acc = options.accuracy;
        let sourcesText = '';

        if (acc.sources_analyzed && acc.sources_analyzed > 0) {
            sourcesText = `<div class="metric">🔍 Sources: ${acc.sources_analyzed}</div>`;
        } else {
            sourcesText = `<div class="metric" title="Web search unavailable, answer generated from AI knowledge">🧠 AI Knowledge</div>`;
        }

        metaHtml = `
            <div class="message-meta">
                <div class="metric">📊 Accuracy: ${acc.overall_accuracy}%</div>
                ${sourcesText}
                ${acc.confidence_level ? `<div class="metric">📈 Confidence: ${acc.confidence_level}</div>` : ''}
            </div>
        `;

        if (options.sources && options.sources.length > 0) {
            const sourcesHtml = options.sources.map((s, i) => {
                const newsBadge = s.is_news ? '<span class="source-badge news">NEWS</span> ' : '';
                return `<li>${newsBadge}<a href="${s.url}" target="_blank">${escapeHtml(s.title)}</a></li>`;
            }).join('');

            metaHtml += `
                <div class="sources">
                    <button class="sources-toggle" onclick="this.nextElementSibling.classList.toggle('hidden')">
                        View ${options.sources.length} sources
                    </button>
                    <ol class="sources-list hidden">${sourcesHtml}</ol>
                </div>
            `;
        }
    }

    messageEl.innerHTML = `
        <div class="message-content">
            ${formatMessage(content)}
            ${metaHtml}
        </div>
    `;

    messagesEl.appendChild(messageEl);

    if (!options.skipScroll) {
        scrollToBottom();
    }
}

// Show typing indicator
function showTypingIndicator() {
    const messagesEl = document.getElementById('chatMessages');
    const indicator = document.createElement('div');
    indicator.className = 'message assistant';
    indicator.id = 'typingIndicator';
    indicator.innerHTML = `
        <div class="message-content">
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    messagesEl.appendChild(indicator);
    scrollToBottom();
}

// Hide typing indicator
function hideTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

// Update active conversation
function updateActiveConversation(id) {
    document.querySelectorAll('.conversation-item').forEach(el => {
        el.classList.remove('active');
        if (parseInt(el.getAttribute('onclick').match(/\d+/)[0]) === id) {
            el.classList.add('active');
        }
    });
}

// Start new chat
function startNewChat() {
    currentConversationId = null;
    document.getElementById('chatMessages').innerHTML = `
        <div class="welcome-message" id="welcomeMessage">
            <h1>🧠 NeuralQuery</h1>
            <p class="subtitle">AI-Powered Research Assistant</p>
            <p>Ask me anything and I'll search multiple sources to give you comprehensive, accurate answers.</p>
        </div>
    `;
    document.querySelectorAll('.conversation-item').forEach(el => el.classList.remove('active'));
    document.getElementById('messageInput').focus();
}

// Hide welcome message
function hideWelcomeMessage() {
    const welcome = document.getElementById('welcomeMessage');
    if (welcome) {
        welcome.remove();
    }
}

// Show/hide loading overlay
function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.remove('hidden');
    } else {
        overlay.classList.add('hidden');
    }
}

// Scroll to bottom of chat
function scrollToBottom() {
    const messagesEl = document.getElementById('chatMessages');
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

// Format message content (basic markdown support)
function formatMessage(text) {
    // Escape HTML first
    let formatted = escapeHtml(text);

    // Convert markdown-style formatting
    formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>'); // Bold
    formatted = formatted.replace(/\*(.+?)\*/g, '<em>$1</em>'); // Italic
    formatted = formatted.replace(/\n/g, '<br>'); // Line breaks

    // Convert links
    formatted = formatted.replace(
        /(https?:\/\/[^\s<]+)/g,
        '<a href="$1" target="_blank">$1</a>'
    );

    return formatted;
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Format date
function formatDate(dateString) {
    if (!dateString) return '';

    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 7) {
        return date.toLocaleDateString();
    } else if (days > 0) {
        return `${days}d ago`;
    } else if (hours > 0) {
        return `${hours}h ago`;
    } else if (minutes > 0) {
        return `${minutes}m ago`;
    } else {
        return 'Just now';
    }
}

// =============================================================================
// EVENT HANDLERS
// =============================================================================

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    // Check authentication
    if (!checkAuth()) return;

    // Load conversations
    loadConversations();

    // Setup event listeners
    setupEventListeners();
});



// Apply theme


// =============================================================================
// UI INTERACTION HANDLERS
// =============================================================================

function setupEventListeners() {
    // New chat button
    document.getElementById('newChatBtn').addEventListener('click', startNewChat);

    // Logout button
    document.getElementById('logoutBtn').addEventListener('click', logout);



    // Search chats
    const searchInput = document.getElementById('searchChats');
    searchInput.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();
        document.querySelectorAll('.conversation-item').forEach(item => {
            const title = item.querySelector('.conversation-title').textContent.toLowerCase();
            if (title.includes(term)) {
                item.style.display = 'flex';
            } else {
                item.style.display = 'none';
            }
        });
    });

    // Message input
    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');

    messageInput.addEventListener('input', () => {
        // Enable/disable send button
        sendBtn.disabled = !messageInput.value.trim();

        // Auto-resize textarea
        messageInput.style.height = 'auto';
        messageInput.style.height = (messageInput.scrollHeight) + 'px';
    });

    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (messageInput.value.trim()) {
                sendMessage();
            }
        }
    });

    // Send button
    sendBtn.addEventListener('click', sendMessage);

    // Example queries
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('example-btn')) {
            const query = e.target.getAttribute('data-query');
            messageInput.value = query;
            sendMessage();
        }
    });

    // File upload button
    document.getElementById('uploadBtn').addEventListener('click', () => {
        document.getElementById('fileInput').click();
    });

    document.getElementById('fileInput').addEventListener('change', handleFileUpload);
}

// Render conversations list (Updated for new HTML structure)
function renderConversations() {
    const listEl = document.getElementById('conversationList');

    if (conversations.length === 0) {
        listEl.innerHTML = `
            <div class="loading-conversations" style="color: var(--sidebar-text-secondary); font-size: 0.8rem;">
                <p>No chats yet.</p>
            </div>
        `;
        return;
    }

    listEl.innerHTML = conversations.map(conv => `
        <div class="conversation-item ${conv.id === currentConversationId ? 'active' : ''}" 
             onclick="loadConversation(${conv.id})">
             <span class="icon-chat">💬</span>
            <div class="conversation-title" title="${escapeHtml(conv.title)}">${escapeHtml(conv.title || 'New Chat')}</div>
        </div>
    `).join('');
}

// Send message
function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const query = messageInput.value.trim();

    if (!query) return;

    // Clear input
    messageInput.value = '';
    messageInput.style.height = 'auto';
    document.getElementById('sendBtn').disabled = true;

    // Send query
    sendQuery(query);
}

// Handle file upload
async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
        alert('File too large. Maximum size is 10MB.');
        return;
    }

    // Validate file type
    const allowedTypes = ['application/pdf', 'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain'];
    if (!allowedTypes.includes(file.type)) {
        alert('File type not supported. Please upload PDF, DOC, DOCX, or TXT files.');
        return;
    }

    showLoading(true);

    try {
        // Upload file
        const formData = new FormData();
        formData.append('file', file);

        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE}/api/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            // Show success message and prompt for question
            addMessage('assistant', `✅ File uploaded: ${file.name}\n\nWhat would you like to know about this document?`);

            // Store extracted text for analysis
            window.lastUploadedText = data.extracted_text;
        } else {
            addMessage('assistant', `❌ Upload failed: ${data.error}`);
        }
    } catch (error) {
        console.error('Upload error:', error);
        addMessage('assistant', '❌ Upload failed. Please try again.');
    } finally {
        showLoading(false);
        e.target.value = ''; // Reset file input
    }
}

// Make functions globally accessible
window.loadConversation = loadConversation;
window.deleteConversation = deleteConversation;
