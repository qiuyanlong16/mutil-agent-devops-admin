let currentAgent = null;
let currentLogType = "gateway.log";
let eventSource = null;
let pollTimer = null;

/* ============================================================
   Agent Actions — vanilla fetch (replaces HTMX hx-post)
   ============================================================ */

async function agentAction(name, action, btnEl) {
    const originalText = btnEl.textContent;
    btnEl.disabled = true;
    btnEl.innerHTML = '<span class="spinner"></span>';

    try {
        const resp = await fetch(`/api/agents/${name}/${action}`, {
            method: 'POST',
        });
        if (resp.ok) {
            refreshAgentList();
        } else {
            // Server error — restore button so user can retry
            btnEl.disabled = false;
            btnEl.textContent = originalText;
            const data = await resp.json().catch(() => ({}));
            console.error(`Action ${action} failed for ${name}:`, data);
        }
    } catch (err) {
        btnEl.disabled = false;
        btnEl.textContent = originalText;
        console.error(`Action ${action} failed for ${name}:`, err);
    }
}

/* ============================================================
   Agent Selection
   ============================================================ */

function selectAgent(name, evt) {
    document.querySelectorAll('.agent-card').forEach(card => {
        card.classList.remove('selected');
    });

    evt.currentTarget.classList.add('selected');

    const logControls = document.getElementById('log-controls');
    logControls.classList.remove('hidden');
    document.getElementById('log-agent-name').textContent = name;

    currentAgent = name;
    startLogStream();
}

/* ============================================================
   Log Tab Switching
   ============================================================ */

function selectLogTab(logType) {
    currentLogType = logType;

    document.querySelectorAll('.log-tab').forEach(tab => {
        if (tab.dataset.logType === logType) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    startLogStream();
}

/* ============================================================
   SSE Log Streaming
   ============================================================ */

function startLogStream() {
    if (!currentAgent) return;

    if (eventSource) {
        eventSource.close();
    }

    const output = document.getElementById('log-output');
    output.innerHTML = '';

    // Load recent lines
    fetch(`/api/logs/${currentAgent}/recent?log_type=${currentLogType}`)
        .then(r => r.json())
        .then(data => {
            if (data.lines) {
                output.innerHTML = formatLogLines(data.lines);
                output.scrollTop = output.scrollHeight;
            }
        })
        .catch(() => {});

    // SSE
    eventSource = new EventSource(
        `/api/logs/${currentAgent}/stream?log_type=${currentLogType}`
    );

    eventSource.addEventListener('log', (e) => {
        const output = document.getElementById('log-output');
        const div = document.createElement('div');
        div.className = 'log-line';
        div.textContent = e.data;
        output.appendChild(div);

        if (output.scrollHeight - output.scrollTop - output.clientHeight < 100) {
            output.scrollTop = output.scrollHeight;
        }

        while (output.children.length > 2000) {
            output.removeChild(output.firstChild);
        }
    });

    eventSource.addEventListener('error', (e) => {
        const output = document.getElementById('log-output');
        const div = document.createElement('div');
        div.style.color = '#f87171';
        div.textContent = e.data;
        output.appendChild(div);
    });
}

function clearLogs() {
    document.getElementById('log-output').innerHTML = '';
}

function formatLogLines(text) {
    return text.split('\n').map(line => {
        return `<div class="log-line">${escapeHtml(line)}</div>`;
    }).join('');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/* ============================================================
   Agent List Polling (replaces HTMX hx-get every 5s)
   ============================================================ */

async function refreshAgentList() {
    try {
        const resp = await fetch('/api/agents');
        const html = await resp.text();
        const agentList = document.getElementById('agent-list');
        if (agentList) {
            agentList.innerHTML = html;

            // Re-highlight selected agent if present
            if (currentAgent) {
                const cards = agentList.querySelectorAll('.agent-card');
                cards.forEach(card => {
                    const onclick = card.getAttribute('onclick');
                    if (onclick && onclick.includes(`'${currentAgent}'`)) {
                        card.classList.add('selected');
                    }
                });
            }
        }
    } catch (err) {
        console.error('Failed to refresh agent list:', err);
    }
}

// Start 5-second polling
function startPolling() {
    pollTimer = setInterval(refreshAgentList, 5000);
}

// Update stats in header after refresh
function updateStats() {
    // Stats are rendered server-side; they get refreshed on full page reload
    // The poll refreshes only agent cards, so stats stay in sync on initial render
}

// Boot
startPolling();
