/**
 * MCP Manager - Handles MCP tool management and usage
 */
class MCPManager {
  constructor() {
    this.connected = false;
    this.availableTools = [];
    this.enabledTools = new Set();
    this.serverInfo = null;
  }

  async initialize() {
    // Check connection status
    await this.checkStatus();

    // If not connected, try to connect
    if (!this.connected) {
      await this.connect();
    }

    this.setupEventListeners();
    console.log('MCPManager initialized');
  }

  setupEventListeners() {
    // Connect button
    const connectBtn = document.getElementById('mcp-connect-btn');
    if (connectBtn) {
      connectBtn.addEventListener('click', () => this.connect());
    }

    // Disconnect button
    const disconnectBtn = document.getElementById('mcp-disconnect-btn');
    if (disconnectBtn) {
      disconnectBtn.addEventListener('click', () => this.disconnect());
    }

    // Test tools button
    const testBtn = document.getElementById('mcp-test-btn');
    if (testBtn) {
      testBtn.addEventListener('click', () => this.testTools());
    }

    // Tool search
    const searchInput = document.getElementById('tool-search');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => this.filterTools(e.target.value));
    }
  }

  async checkStatus() {
    try {
      const response = await fetch('/api/mcp/status');
      const data = await response.json();

      this.connected = data.connected;
      this.serverInfo = data.server_info;

      this.updateConnectionUI();

      if (this.connected) {
        await this.loadTools();
      }
    } catch (error) {
      console.error('Failed to check MCP status:', error);
    }
  }

  async connect() {
    try {
      const response = await fetch('/api/mcp/connect', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          server_path: 'services/mcp_server.py'
        })
      });

      const data = await response.json();

      if (data.success) {
        this.connected = true;
        this.serverInfo = data.server_info;
        this.availableTools = data.tools || [];

        this.updateConnectionUI();
        this.renderToolsList();

        this.showNotification('✓ Connected to MCP server', 'success');
      } else {
        this.showNotification('✗ Failed to connect to MCP server', 'error');
      }
    } catch (error) {
      console.error('Connection failed:', error);
      this.showNotification('✗ Connection error: ' + error.message, 'error');
    }
  }

  async disconnect() {
    try {
      const response = await fetch('/api/mcp/disconnect', {
        method: 'POST'
      });

      const data = await response.json();

      if (data.success) {
        this.connected = false;
        this.serverInfo = null;
        this.availableTools = [];
        this.enabledTools.clear();

        this.updateConnectionUI();
        this.renderToolsList();

        this.showNotification('Disconnected from MCP server', 'info');
      }
    } catch (error) {
      console.error('Disconnect failed:', error);
    }
  }

  async loadTools() {
    try {
      const response = await fetch('/api/mcp/tools');
      const data = await response.json();

      if (data.tools) {
        this.availableTools = data.tools;
        this.renderToolsList();
      }
    } catch (error) {
      console.error('Failed to load tools:', error);
    }
  }

  async callTool(toolName, arguments) {
    try {
      const response = await fetch(`/api/mcp/tools/${toolName}/call`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({arguments})
      });

      const data = await response.json();
      return data;
    } catch (error) {
      console.error(`Failed to call tool ${toolName}:`, error);
      return {success: false, error: error.message};
    }
  }

  async testTools() {
    this.showNotification('Testing MCP tools...', 'info');

    try {
      const response = await fetch('/api/mcp/test', {
        method: 'POST'
      });

      const data = await response.json();

      const passed = data.passed || 0;
      const total = data.total_tests || 0;

      if (passed === total) {
        this.showNotification(`✓ All ${total} tests passed!`, 'success');
      } else {
        this.showNotification(`⚠ ${passed}/${total} tests passed`, 'warning');
      }

      console.log('Test results:', data.test_results);
    } catch (error) {
      this.showNotification('✗ Test failed: ' + error.message, 'error');
    }
  }

  updateConnectionUI() {
    const statusEl = document.getElementById('mcp-status');
    const connectBtn = document.getElementById('mcp-connect-btn');
    const disconnectBtn = document.getElementById('mcp-disconnect-btn');

    if (statusEl) {
      if (this.connected) {
        statusEl.innerHTML = `
          <span class="status-badge connected">● Connected</span>
          <span class="server-name">${this.serverInfo?.name || 'MCP Server'}</span>
        `;
      } else {
        statusEl.innerHTML = `
          <span class="status-badge disconnected">○ Disconnected</span>
        `;
      }
    }

    if (connectBtn) {
      connectBtn.style.display = this.connected ? 'none' : 'inline-block';
    }

    if (disconnectBtn) {
      disconnectBtn.style.display = this.connected ? 'inline-block' : 'none';
    }
  }

  renderToolsList() {
    const container = document.getElementById('tools-list');
    if (!container) return;

    if (!this.connected || this.availableTools.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          ${this.connected ? 'No tools available' : 'Not connected to MCP server'}
        </div>
      `;
      return;
    }

    // Categorize tools
    const categories = this.categorizeTools(this.availableTools);

    let html = '';

    for (const [category, tools] of Object.entries(categories)) {
      if (tools.length === 0) continue;

      html += `<div class="tool-category">
        <h4 class="category-title">${category}</h4>
        <div class="tool-items">`;

      for (const tool of tools) {
        const isEnabled = this.enabledTools.has(tool.name);

        html += `
          <div class="tool-item ${isEnabled ? 'enabled' : ''}" data-tool="${tool.name}">
            <div class="tool-header">
              <label class="tool-toggle">
                <input type="checkbox"
                       ${isEnabled ? 'checked' : ''}
                       onchange="mcpManager.toggleTool('${tool.name}', this.checked)">
                <span class="toggle-slider"></span>
              </label>
              <div class="tool-info">
                <div class="tool-name">${tool.name}</div>
                <div class="tool-description">${tool.description || 'No description'}</div>
              </div>
              <button class="tool-expand-btn" onclick="mcpManager.toggleToolDetails('${tool.name}')">
                ⌄
              </button>
            </div>
            <div class="tool-details" id="tool-details-${tool.name}" style="display: none;">
              <div class="tool-parameters">
                <strong>Parameters:</strong>
                <pre>${JSON.stringify(tool.parameters, null, 2)}</pre>
              </div>
              <button class="tool-test-btn" onclick="mcpManager.showToolTester('${tool.name}')">
                Test Tool
              </button>
            </div>
          </div>
        `;
      }

      html += `</div></div>`;
    }

    container.innerHTML = html;
  }

  categorizeTools(tools) {
    const categories = {
      'Math': [],
      'Text': [],
      'Date/Time': [],
      'Files': [],
      'Web': [],
      'Image': [],
      'Other': []
    };

    for (const tool of tools) {
      const name = tool.name.toLowerCase();

      if (name.includes('add') || name.includes('multiply') || name.includes('calculate')) {
        categories['Math'].push(tool);
      } else if (name.includes('text') || name.includes('word') || name.includes('char') || name.includes('case')) {
        categories['Text'].push(tool);
      } else if (name.includes('time') || name.includes('date') || name.includes('day')) {
        categories['Date/Time'].push(tool);
      } else if (name.includes('file') || name.includes('read') || name.includes('list')) {
        categories['Files'].push(tool);
      } else if (name.includes('web') || name.includes('url') || name.includes('fetch') || name.includes('search')) {
        categories['Web'].push(tool);
      } else if (name.includes('image') || name.includes('generate')) {
        categories['Image'].push(tool);
      } else {
        categories['Other'].push(tool);
      }
    }

    return categories;
  }

  toggleTool(toolName, enabled) {
    if (enabled) {
      this.enabledTools.add(toolName);
    } else {
      this.enabledTools.delete(toolName);
    }

    // Save to current session if available
    if (sessionManager && sessionManager.currentSessionId) {
      this.saveSessionTools(sessionManager.currentSessionId);
    }

    console.log(`Tool ${toolName} ${enabled ? 'enabled' : 'disabled'}`);
  }

  async saveSessionTools(sessionId) {
    try {
      await fetch(`/api/mcp/session/${sessionId}/tools`, {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          enabled_tools: Array.from(this.enabledTools)
        })
      });
    } catch (error) {
      console.error('Failed to save session tools:', error);
    }
  }

  async loadSessionTools(sessionId) {
    try {
      const response = await fetch(`/api/mcp/session/${sessionId}/tools`);
      const data = await response.json();

      if (data.enabled_tools) {
        this.enabledTools = new Set(data.enabled_tools);
        this.renderToolsList();
      }
    } catch (error) {
      console.error('Failed to load session tools:', error);
    }
  }

  toggleToolDetails(toolName) {
    const details = document.getElementById(`tool-details-${toolName}`);
    const button = event.target;

    if (details) {
      if (details.style.display === 'none') {
        details.style.display = 'block';
        button.textContent = '⌃';
      } else {
        details.style.display = 'none';
        button.textContent = '⌄';
      }
    }
  }

  showToolTester(toolName) {
    const tool = this.availableTools.find(t => t.name === toolName);
    if (!tool) return;

    const modal = document.createElement('div');
    modal.className = 'tool-tester-modal';
    modal.innerHTML = `
      <div class="modal-content">
        <div class="modal-header">
          <h3>Test Tool: ${toolName}</h3>
          <button class="close-btn" onclick="this.closest('.tool-tester-modal').remove()">✕</button>
        </div>
        <div class="modal-body">
          <div class="tool-tester-form" id="tester-form-${toolName}">
            <!-- Form fields will be generated here -->
          </div>
          <button class="btn-primary" onclick="mcpManager.executeToolTest('${toolName}')">
            Execute
          </button>
        </div>
        <div class="modal-footer">
          <div id="tool-result-${toolName}" class="tool-result"></div>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    // Generate form fields based on parameters
    this.generateToolForm(toolName, tool.parameters);
  }

  generateToolForm(toolName, parameters) {
    const form = document.getElementById(`tester-form-${toolName}`);
    if (!form || !parameters || !parameters.properties) return;

    let html = '';

    for (const [paramName, paramInfo] of Object.entries(parameters.properties)) {
      const type = paramInfo.type || 'string';
      const description = paramInfo.description || '';
      const required = parameters.required?.includes(paramName) || false;

      html += `
        <div class="form-field">
          <label>
            ${paramName} ${required ? '<span class="required">*</span>' : ''}
            <span class="field-type">(${type})</span>
          </label>
          <input type="${type === 'number' ? 'number' : 'text'}"
                 id="param-${toolName}-${paramName}"
                 placeholder="${description}"
                 ${required ? 'required' : ''}>
        </div>
      `;
    }

    form.innerHTML = html;
  }

  async executeToolTest(toolName) {
    const tool = this.availableTools.find(t => t.name === toolName);
    if (!tool) return;

    // Collect form values
    const args = {};
    const params = tool.parameters?.properties || {};

    for (const paramName of Object.keys(params)) {
      const input = document.getElementById(`param-${toolName}-${paramName}`);
      if (input && input.value) {
        const type = params[paramName].type;
        args[paramName] = type === 'number' ? parseFloat(input.value) : input.value;
      }
    }

    // Call tool
    const resultDiv = document.getElementById(`tool-result-${toolName}`);
    if (resultDiv) {
      resultDiv.innerHTML = '<div class="loading">Executing...</div>';
    }

    const result = await this.callTool(toolName, args);

    if (resultDiv) {
      if (result.success) {
        resultDiv.innerHTML = `
          <div class="result-success">
            <strong>Result:</strong>
            <pre>${JSON.stringify(result.result, null, 2)}</pre>
          </div>
        `;
      } else {
        resultDiv.innerHTML = `
          <div class="result-error">
            <strong>Error:</strong> ${result.error}
          </div>
        `;
      }
    }
  }

  filterTools(query) {
    const items = document.querySelectorAll('.tool-item');

    if (!query) {
      items.forEach(item => item.style.display = '');
      return;
    }

    const lowerQuery = query.toLowerCase();

    items.forEach(item => {
      const toolName = item.dataset.tool.toLowerCase();
      const description = item.querySelector('.tool-description')?.textContent.toLowerCase() || '';

      if (toolName.includes(lowerQuery) || description.includes(lowerQuery)) {
        item.style.display = '';
      } else {
        item.style.display = 'none';
      }
    });
  }

  showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
      notification.classList.add('show');
    }, 10);

    setTimeout(() => {
      notification.classList.remove('show');
      setTimeout(() => notification.remove(), 300);
    }, 3000);
  }

  getEnabledTools() {
    return Array.from(this.enabledTools);
  }

  isToolEnabled(toolName) {
    return this.enabledTools.has(toolName);
  }
}

// Global instance
const mcpManager = new MCPManager();

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  // Initialize after a short delay to ensure DOM is ready
  setTimeout(() => {
    mcpManager.initialize();
  }, 100);
});
