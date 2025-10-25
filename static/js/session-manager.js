/**
 * Session Manager - Handles chat session management
 */
class SessionManager {
  constructor() {
    this.currentSessionId = null;
    this.sessions = [];
    this.userId = 'default-user';
    this.initialized = false;
  }

  async initialize() {
    if (this.initialized) return;

    await this.loadSessions();
    this.setupEventListeners();
    this.initialized = true;

    console.log('SessionManager initialized');
  }

  setupEventListeners() {
    // New chat button
    const newChatBtn = document.getElementById('new-chat-btn');
    if (newChatBtn) {
      newChatBtn.addEventListener('click', () => this.createNewSession());
    }

    // Search input
    const searchInput = document.getElementById('session-search');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => this.handleSearch(e.target.value));
    }

    // Toggle sidebar
    const toggleBtn = document.getElementById('toggle-sidebar-btn');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => this.toggleSidebar());
    }
  }

  async loadSessions() {
    try {
      const response = await fetch(`/api/sessions?user_id=${this.userId}`);
      const data = await response.json();
      this.sessions = data.sessions || [];
      this.renderSessionList();

      // Load first session if none is selected
      if (!this.currentSessionId && this.sessions.length > 0) {
        await this.loadSession(this.sessions[0].id);
      }
    } catch (error) {
      console.error('Failed to load sessions:', error);
      this.showError('Failed to load sessions');
    }
  }

  async createNewSession() {
    try {
      const modelSelect = document.getElementById('model-select');
      const modelName = modelSelect ? modelSelect.value : 'llama2';

      const response = await fetch('/api/sessions', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          user_id: this.userId,
          model_name: modelName,
          mode: 'chat'
        })
      });

      const data = await response.json();
      this.currentSessionId = data.session.id;

      // Clear chat messages
      this.clearChatMessages();

      await this.loadSessions();

      console.log('New session created:', data.session.id);
    } catch (error) {
      console.error('Failed to create session:', error);
      this.showError('Failed to create new session');
    }
  }

  async loadSession(sessionId) {
    try {
      const response = await fetch(`/api/sessions/${sessionId}`);
      const data = await response.json();

      this.currentSessionId = sessionId;
      this.loadMessagesIntoChat(data.messages || []);
      this.renderSessionList();

      // Update model selection if available
      if (data.model_name) {
        const modelSelect = document.getElementById('model-select');
        if (modelSelect) {
          modelSelect.value = data.model_name;
        }
      }

      console.log('Session loaded:', sessionId);
    } catch (error) {
      console.error('Failed to load session:', error);
      this.showError('Failed to load session');
    }
  }

  async deleteSession(sessionId) {
    if (!confirm('Are you sure you want to delete this conversation?')) {
      return;
    }

    try {
      await fetch(`/api/sessions/${sessionId}`, {method: 'DELETE'});

      // If deleted current session, create new one
      if (sessionId === this.currentSessionId) {
        await this.createNewSession();
      } else {
        await this.loadSessions();
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
      this.showError('Failed to delete session');
    }
  }

  async renameSession(sessionId, newTitle) {
    try {
      await fetch(`/api/sessions/${sessionId}`, {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({title: newTitle})
      });

      await this.loadSessions();
    } catch (error) {
      console.error('Failed to rename session:', error);
      this.showError('Failed to rename session');
    }
  }

  async togglePin(sessionId) {
    try {
      await fetch(`/api/sessions/${sessionId}`, {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({pinned: true})
      });

      await this.loadSessions();
    } catch (error) {
      console.error('Failed to toggle pin:', error);
      this.showError('Failed to pin/unpin session');
    }
  }

  async archiveSession(sessionId) {
    try {
      await fetch(`/api/sessions/${sessionId}`, {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({archived: true})
      });

      await this.loadSessions();
    } catch (error) {
      console.error('Failed to archive session:', error);
      this.showError('Failed to archive session');
    }
  }

  async handleSearch(query) {
    if (!query || query.trim().length === 0) {
      await this.loadSessions();
      return;
    }

    try {
      const response = await fetch(`/api/sessions/search?user_id=${this.userId}&q=${encodeURIComponent(query)}`);
      const data = await response.json();
      this.sessions = data.sessions || [];
      this.renderSessionList();
    } catch (error) {
      console.error('Search failed:', error);
    }
  }

  renderSessionList() {
    const sidebar = document.getElementById('session-list');
    if (!sidebar) return;

    const grouped = this.groupSessions(this.sessions);
    let html = '';

    for (const [groupName, sessions] of Object.entries(grouped)) {
      if (sessions.length === 0) continue;

      html += `<div class="session-group">
        <h4 class="group-title">${groupName}</h4>`;

      for (const session of sessions) {
        const isActive = session.id === this.currentSessionId;
        const icon = this.getSessionIcon(session.mode);

        html += `
          <div class="session-item ${isActive ? 'active' : ''} ${session.pinned ? 'pinned' : ''}"
               data-session-id="${session.id}">
            <div class="session-icon">${icon}</div>
            <div class="session-content">
              <div class="session-title" title="${this.escapeHtml(session.title)}">
                ${this.escapeHtml(session.title)}
              </div>
              <div class="session-meta">
                ${session.message_count || 0} messages
              </div>
            </div>
            <div class="session-actions">
              <button class="action-btn pin-btn" onclick="sessionManager.togglePin('${session.id}')" title="${session.pinned ? 'Unpin' : 'Pin'}">
                ${session.pinned ? '📌' : '📍'}
              </button>
              <button class="action-btn more-btn" onclick="sessionManager.showContextMenu(event, '${session.id}')">
                ⋮
              </button>
            </div>
          </div>`;
      }

      html += '</div>';
    }

    if (html === '') {
      html = '<div class="empty-state">No conversations yet. Click "New Chat" to start!</div>';
    }

    sidebar.innerHTML = html;

    // Add click listeners to session items
    document.querySelectorAll('.session-item').forEach(item => {
      item.addEventListener('click', (e) => {
        if (!e.target.closest('.session-actions')) {
          this.loadSession(item.dataset.sessionId);
        }
      });
    });
  }

  showContextMenu(event, sessionId) {
    event.stopPropagation();

    const menu = document.getElementById('session-context-menu');
    if (!menu) {
      this.createContextMenu();
      return this.showContextMenu(event, sessionId);
    }

    menu.dataset.sessionId = sessionId;
    menu.style.display = 'block';
    menu.style.left = event.pageX + 'px';
    menu.style.top = event.pageY + 'px';

    // Close menu when clicking outside
    setTimeout(() => {
      document.addEventListener('click', () => {
        menu.style.display = 'none';
      }, {once: true});
    }, 0);
  }

  createContextMenu() {
    const menu = document.createElement('div');
    menu.id = 'session-context-menu';
    menu.className = 'context-menu';
    menu.innerHTML = `
      <div class="context-menu-item" onclick="sessionManager.renameSessionPrompt()">
        ✏️ Rename
      </div>
      <div class="context-menu-item" onclick="sessionManager.archiveSessionFromMenu()">
        📦 Archive
      </div>
      <div class="context-menu-item danger" onclick="sessionManager.deleteSessionFromMenu()">
        🗑️ Delete
      </div>
    `;
    document.body.appendChild(menu);
  }

  renameSessionPrompt() {
    const menu = document.getElementById('session-context-menu');
    const sessionId = menu.dataset.sessionId;
    const session = this.sessions.find(s => s.id === sessionId);

    const newTitle = prompt('Enter new name:', session ? session.title : '');
    if (newTitle && newTitle.trim()) {
      this.renameSession(sessionId, newTitle.trim());
    }
  }

  archiveSessionFromMenu() {
    const menu = document.getElementById('session-context-menu');
    this.archiveSession(menu.dataset.sessionId);
  }

  deleteSessionFromMenu() {
    const menu = document.getElementById('session-context-menu');
    this.deleteSession(menu.dataset.sessionId);
  }

  groupSessions(sessions) {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const last7Days = new Date(today);
    last7Days.setDate(last7Days.getDate() - 7);
    const last30Days = new Date(today);
    last30Days.setDate(last30Days.getDate() - 30);

    const grouped = {
      'Pinned': [],
      'Today': [],
      'Yesterday': [],
      'Previous 7 Days': [],
      'Previous 30 Days': [],
      'Older': []
    };

    for (const session of sessions) {
      const updated = new Date(session.updated_at);

      if (session.pinned) {
        grouped['Pinned'].push(session);
      } else if (updated >= today) {
        grouped['Today'].push(session);
      } else if (updated >= yesterday) {
        grouped['Yesterday'].push(session);
      } else if (updated >= last7Days) {
        grouped['Previous 7 Days'].push(session);
      } else if (updated >= last30Days) {
        grouped['Previous 30 Days'].push(session);
      } else {
        grouped['Older'].push(session);
      }
    }

    return grouped;
  }

  getSessionIcon(mode) {
    const icons = {
      'chat': '💬',
      'image_gen': '🖼️',
      'img2img': '🎨'
    };
    return icons[mode] || '💬';
  }

  loadMessagesIntoChat(messages) {
    this.clearChatMessages();

    for (const msg of messages) {
      this.addMessageToChat(msg);
    }
  }

  clearChatMessages() {
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
      chatMessages.innerHTML = '';
    }
  }

  addMessageToChat(message) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${message.role}`;

    let agentBadge = '';
    if (message.agent_name) {
      agentBadge = `<div class="agent-badge">${message.agent_name}</div>`;
    }

    let toolInfo = '';
    if (message.tool_calls) {
      toolInfo = `<div class="tool-info">🔧 Used tools</div>`;
    }

    let imageContent = '';
    if (message.image_url) {
      imageContent = `<img src="${message.image_url}" class="message-image" alt="Image">`;
    }

    messageDiv.innerHTML = `
      ${agentBadge}
      <div class="message-content">${this.formatContent(message.content)}</div>
      ${imageContent}
      ${toolInfo}
    `;

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  formatContent(content) {
    if (!content) return '';

    // Simple markdown-like formatting
    return content
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\n/g, '<br>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>');
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  toggleSidebar() {
    const sidebar = document.getElementById('session-sidebar');
    const mainContent = document.querySelector('.main-content');

    if (sidebar && mainContent) {
      sidebar.classList.toggle('collapsed');
      mainContent.classList.toggle('sidebar-collapsed');
    }
  }

  showError(message) {
    console.error(message);
    // You can implement a toast notification here
    alert(message);
  }

  // Method to save message to current session
  async saveMessage(role, content, imageUrl = null, agentName = null, toolCalls = null) {
    if (!this.currentSessionId) {
      // Create new session if none exists
      await this.createNewSession();
    }

    try {
      const response = await fetch(`/api/sessions/${this.currentSessionId}/messages`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          role,
          content,
          image_url: imageUrl,
          agent_name: agentName,
          tool_calls: toolCalls
        })
      });

      const data = await response.json();

      // Refresh session list to update message count
      await this.loadSessions();

      return data.message;
    } catch (error) {
      console.error('Failed to save message:', error);
      throw error;
    }
  }
}

// Global instance
const sessionManager = new SessionManager();

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  sessionManager.initialize();
});
