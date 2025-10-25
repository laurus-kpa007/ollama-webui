/**
 * Autogen Manager - Multi-agent system management
 */
class AutogenManager {
  constructor() {
    this.agents = [];
    this.selectedAgents = new Set();
    this.workflows = [];
  }

  async initialize() {
    await this.loadAgents();
    await this.loadWorkflows();
    this.setupEventListeners();
    console.log('AutogenManager initialized');
  }

  setupEventListeners() {
    const runBtn = document.getElementById('run-agents-btn');
    if (runBtn) {
      runBtn.addEventListener('click', () => this.runAgentTask());
    }

    const testBtn = document.getElementById('test-agents-btn');
    if (testBtn) {
      testBtn.addEventListener('click', () => this.testAgents());
    }
  }

  async loadAgents() {
    try {
      const response = await fetch('/api/autogen/agents');
      const data = await response.json();
      this.agents = data.agents || [];
      this.renderAgentsList();
    } catch (error) {
      console.error('Failed to load agents:', error);
    }
  }

  async loadWorkflows() {
    try {
      const response = await fetch('/api/autogen/workflows');
      const data = await response.json();
      this.workflows = data.workflows || [];
      this.renderWorkflowsList();
    } catch (error) {
      console.error('Failed to load workflows:', error);
    }
  }

  renderAgentsList() {
    const container = document.getElementById('agents-list');
    if (!container) return;

    if (this.agents.length === 0) {
      container.innerHTML = '<div class="empty-state">No agents available</div>';
      return;
    }

    let html = '';
    for (const agent of this.agents) {
      const isSelected = this.selectedAgents.has(agent.name);
      html += `
        <div class="agent-card ${isSelected ? 'selected' : ''}" data-agent="${agent.name}">
          <div class="agent-header">
            <label class="agent-checkbox">
              <input type="checkbox" ${isSelected ? 'checked' : ''}
                     onchange="autogenManager.toggleAgent('${agent.name}', this.checked)">
              <span class="agent-name">${agent.name}</span>
            </label>
          </div>
          <div class="agent-description">${agent.system_message.substring(0, 150)}...</div>
        </div>
      `;
    }

    container.innerHTML = html;
  }

  renderWorkflowsList() {
    const container = document.getElementById('workflows-list');
    if (!container) return;

    let html = '';
    for (const workflow of this.workflows) {
      html += `
        <div class="workflow-card" onclick="autogenManager.selectWorkflow('${workflow.id}')">
          <h4>${workflow.name}</h4>
          <p>${workflow.description}</p>
          <div class="workflow-agents">
            ${workflow.recommended_agents.join(', ')}
          </div>
        </div>
      `;
    }

    container.innerHTML = html;
  }

  toggleAgent(agentName, selected) {
    if (selected) {
      this.selectedAgents.add(agentName);
    } else {
      this.selectedAgents.delete(agentName);
    }
    this.renderAgentsList();
  }

  selectWorkflow(workflowId) {
    const workflow = this.workflows.find(w => w.id === workflowId);
    if (workflow) {
      this.selectedAgents = new Set(workflow.recommended_agents);
      this.renderAgentsList();

      const modeSelect = document.getElementById('agent-mode');
      if (modeSelect) {
        modeSelect.value = workflowId === 'group' ? 'group' : 'sequential';
      }
    }
  }

  async runAgentTask() {
    const taskInput = document.getElementById('agent-task');
    const modeSelect = document.getElementById('agent-mode');

    if (!taskInput || !modeSelect) return;

    const task = taskInput.value.trim();
    const mode = modeSelect.value;

    if (!task) {
      alert('Please enter a task');
      return;
    }

    if (this.selectedAgents.size === 0) {
      alert('Please select at least one agent');
      return;
    }

    const resultDiv = document.getElementById('agent-result');
    if (resultDiv) {
      resultDiv.innerHTML = '<div class="loading">Processing...</div>';
    }

    try {
      const endpoint = mode === 'group' ? '/api/autogen/task/group' : '/api/autogen/task/sequential';

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          task,
          agents: Array.from(this.selectedAgents)
        })
      });

      const result = await response.json();

      if (resultDiv) {
        this.displayResult(result, resultDiv);
      }
    } catch (error) {
      if (resultDiv) {
        resultDiv.innerHTML = `<div class="error">Error: ${error.message}</div>`;
      }
    }
  }

  displayResult(result, container) {
    let html = `
      <div class="result-header">
        <strong>Mode:</strong> ${result.mode || 'unknown'}
      </div>
      <div class="result-body">
    `;

    if (result.conversation) {
      html += '<h4>Conversation:</h4>';
      for (const msg of result.conversation) {
        html += `
          <div class="conv-message">
            <strong>${msg.agent || msg.name}:</strong>
            <div>${msg.message || msg.content || ''}</div>
          </div>
        `;
      }
    }

    html += `
        <h4>Final Result:</h4>
        <div class="final-result">${result.final_result || 'No result'}</div>
      </div>
    `;

    container.innerHTML = html;
  }

  async testAgents() {
    const resultDiv = document.getElementById('agent-result');
    if (resultDiv) {
      resultDiv.innerHTML = '<div class="loading">Testing...</div>';
    }

    try {
      const response = await fetch('/api/autogen/test', {method: 'POST'});
      const result = await response.json();

      if (resultDiv) {
        resultDiv.innerHTML = `
          <div class="${result.success ? 'result-success' : 'result-error'}">
            <h4>Test Result:</h4>
            <pre>${JSON.stringify(result, null, 2)}</pre>
          </div>
        `;
      }
    } catch (error) {
      if (resultDiv) {
        resultDiv.innerHTML = `<div class="error">Error: ${error.message}</div>`;
      }
    }
  }
}

const autogenManager = new AutogenManager();

document.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => autogenManager.initialize(), 150);
});
