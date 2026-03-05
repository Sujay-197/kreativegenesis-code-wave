export interface RequirementsState {
  auth: { label: string; value: string | null; confidence: number };
  data: { label: string; value: string | null; confidence: number };
  ui: { label: string; value: string | null; confidence: number };
  logic: { label: string; value: string | null; confidence: number };
  integrations: { label: string; value: string | null; confidence: number };
}

/** @deprecated Use RequirementsState instead */
export type RequirementsObject = RequirementsState;

export interface ConversationMessage {
  role: 'user' | 'ai';
  content: string;
}

export const initialRequirements = (): RequirementsState => ({
  auth: { label: 'Auth & Users', value: null, confidence: 0 },
  data: { label: 'Data & Storage', value: null, confidence: 0 },
  ui: { label: 'UI Complexity', value: null, confidence: 0 },
  logic: { label: 'Business Logic', value: null, confidence: 0 },
  integrations: { label: 'Integrations', value: null, confidence: 0 },
});

export const getOverallConfidence = (req: RequirementsState): number => {
  const values = Object.values(req);
  return values.reduce((sum, d) => sum + d.confidence, 0) / values.length;
};

const simpleOpenings = [
  "Hi! I'm here to help you build your app. What problem are you trying to solve, or what would you like your app to do?",
];

const expertOpenings = [
  "Ready to build. Describe your system — what's the core domain, primary entities, and intended user base?",
];

function extractAppName(history: ConversationMessage[]): string {
  const allText = history.map((m) => m.content).join(' ');
  const patterns = [
    /(?:call(?:ed)?|name(?:d)?|call it)\s+["']?([A-Z][a-zA-Z\s]{2,20})["']?/i,
    /(?:app|system|tool|platform)\s+(?:called|named)\s+["']?([A-Z][a-zA-Z\s]{2,20})["']?/i,
  ];
  for (const p of patterns) {
    const m = allText.match(p);
    if (m) return m[1].trim();
  }
  return '';
}

function inferRequirements(history: ConversationMessage[]): RequirementsState {
  const allText = history
    .filter((m) => m.role === 'user')
    .map((m) => m.content.toLowerCase())
    .join(' ');

  const req: RequirementsState = initialRequirements();

  if (allText.match(/login|sign.?in|user|account|auth|password|role|admin|staff|customer/)) {
    req.auth = {
      label: 'Auth & Users',
      value: allText.match(/admin|staff|role/)
        ? 'Role-based access (admin + standard users)'
        : 'Basic user authentication',
      confidence: 75,
    };
  } else if (allText.match(/just\s*me|only\s*me|personal|my\s*own|solo|single\s*user|myself|no\s*login|no\s*auth|private|individual/)) {
    req.auth = {
      label: 'Auth & Users',
      value: 'Single user, no authentication needed',
      confidence: 85,
    };
  }

  if (allText.match(/order|product|inventory|record|track|list|store|save|data|customer|item|entry|calori|food|meal|nutrition|diet|exercise|workout|weight|habit|budget|expense|task|todo|note|log/)) {
    const entities: string[] = [];
    if (allText.match(/order/)) entities.push('Orders');
    if (allText.match(/customer|client/)) entities.push('Customers');
    if (allText.match(/product|item|inventory/)) entities.push('Products');
    if (allText.match(/appointment|booking/)) entities.push('Appointments');
    if (allText.match(/employee|staff/)) entities.push('Staff');
    if (allText.match(/calori|food|meal|nutrition/)) entities.push('Meals');
    if (allText.match(/exercise|workout/)) entities.push('Workouts');
    if (allText.match(/weight/)) entities.push('Weight Logs');
    if (allText.match(/budget|expense/)) entities.push('Expenses');
    if (allText.match(/task|todo/)) entities.push('Tasks');
    if (allText.match(/habit/)) entities.push('Habits');
    if (allText.match(/note|log/)) entities.push('Notes');
    req.data = {
      label: 'Data & Storage',
      value: entities.length > 0 ? `Entities: ${entities.join(', ')}` : 'Local data storage with CRUD operations',
      confidence: entities.length > 0 ? 80 : 50,
    };
  }

  if (allText.match(/dashboard|chart|report|table|form|list|card|calendar|kanban|view/)) {
    req.ui = {
      label: 'UI Complexity',
      value: allText.match(/dashboard|chart|report/)
        ? 'Multi-view dashboard with data visualization'
        : 'Standard CRUD interface with forms and lists',
      confidence: 70,
    };
  } else if (history.filter((m) => m.role === 'user').length >= 2) {
    req.ui = {
      label: 'UI Complexity',
      value: 'Clean single-page interface with core functionality',
      confidence: 40,
    };
  }

  if (allText.match(/notify|alert|status|workflow|approve|reject|assign|automat|trigger|email|sms/)) {
    req.logic = {
      label: 'Business Logic',
      value: allText.match(/approve|reject|workflow/)
        ? 'Approval workflow with status transitions'
        : 'Status tracking and notification logic',
      confidence: 65,
    };
  } else if (allText.match(/calculate|total|sum|price|cost|tax|discount/)) {
    req.logic = {
      label: 'Business Logic',
      value: 'Calculation and pricing logic',
      confidence: 70,
    };
  } else if (allText.match(/goal|target|limit|daily|weekly|streak|progress/)) {
    req.logic = {
      label: 'Business Logic',
      value: 'Goal tracking with progress toward daily/weekly targets',
      confidence: 65,
    };
  }

  if (allText.match(/payment|stripe|paypal|whatsapp|sms|email|map|google|api|webhook/)) {
    req.integrations = {
      label: 'Integrations',
      value: allText.match(/payment|stripe|paypal/)
        ? 'Payment processing integration'
        : 'Third-party API integration',
      confidence: 60,
    };
  } else if (history.filter((m) => m.role === 'user').length >= 3) {
    req.integrations = {
      label: 'Integrations',
      value: 'No external integrations required',
      confidence: 80,
    };
  }

  return req;
}

function generateNextQuestion(
  history: ConversationMessage[],
  requirements: RequirementsState,
  mode: 'simple' | 'expert'
): string {
  const userMessages = history.filter((m) => m.role === 'user');
  const count = userMessages.length;

  if (count === 0) {
    return mode === 'simple' ? simpleOpenings[0] : expertOpenings[0];
  }

  const allText = userMessages.map((m) => m.content.toLowerCase()).join(' ');

  if (requirements.auth.confidence < 50 && count >= 1) {
    return mode === 'simple'
      ? 'Will different people use this app, or is it just for you? For example, do you need staff logins or customer accounts?'
      : 'Define the authentication model: single-user, multi-user with RBAC, or public-facing with session management?';
  }

  if (requirements.data.confidence < 50 && count >= 1) {
    return mode === 'simple'
      ? 'What kind of information does your app need to keep track of? For example, customers, orders, appointments, or products?'
      : 'Enumerate your primary data entities and their key attributes. What are the core relationships?';
  }

  if (requirements.ui.confidence < 50 && count >= 2) {
    return mode === 'simple'
      ? 'How do you imagine using this app day-to-day? Would you mainly be adding new records, viewing a list, or checking a summary dashboard?'
      : 'Describe the primary views: CRUD tables, dashboard with metrics, kanban board, calendar, or custom layout?';
  }

  if (requirements.logic.confidence < 50 && count >= 2) {
    return mode === 'simple'
      ? 'Are there any rules or steps the app should follow automatically? For example, sending a notification when an order is placed, or changing a status when something is done?'
      : 'Define the core business logic: state machines, computed fields, validation rules, or automated triggers?';
  }

  if (requirements.integrations.confidence < 50 && count >= 3) {
    return mode === 'simple'
      ? 'Does this app need to connect to anything else — like taking payments, sending emails or SMS, or pulling data from another service?'
      : 'List required external integrations: payment gateways, messaging APIs, third-party data sources, or webhooks?';
  }

  if (count >= 4 && !allText.match(/mobile|desktop|tablet|device/)) {
    return mode === 'simple'
      ? 'Will people mostly use this on their phone, on a computer, or both?'
      : 'Target platform: mobile-first PWA, desktop web app, or responsive across all viewports?';
  }

  return mode === 'simple'
    ? "Is there anything else important about how this app should work that we haven't covered yet?"
    : 'Any additional constraints, performance requirements, or edge cases to specify before generation?';
}

export function getOpeningMessage(mode: 'simple' | 'expert'): string {
  return mode === 'simple' ? simpleOpenings[0] : expertOpenings[0];
}

export function processUserMessage(
  userMessage: string,
  history: ConversationMessage[],
  currentRequirements: RequirementsState,
  mode: 'simple' | 'expert'
): { nextQuestion: string; updatedRequirements: RequirementsState; appName: string; isReady: boolean } {
  const updatedHistory: ConversationMessage[] = [
    ...history,
    { role: 'user', content: userMessage },
  ];

  const updatedRequirements = inferRequirements(updatedHistory);
  const appName = extractAppName(updatedHistory);
  const confidence = getOverallConfidence(updatedRequirements);
  const userCount = updatedHistory.filter((m) => m.role === 'user').length;
  const isReady = confidence >= 60 && userCount >= 5;

  const nextQuestion = isReady
    ? ''
    : generateNextQuestion(updatedHistory, updatedRequirements, mode);

  return { nextQuestion, updatedRequirements, appName, isReady };
}

export function generateAppHTML(
  requirements: RequirementsState,
  appName: string,
  mode: 'simple' | 'expert'
): string {
  const name = appName || 'My App';
  const hasAuth = requirements.auth.confidence > 50;
  const hasData = requirements.data.confidence > 50;
  const hasDashboard = requirements.ui.value?.toLowerCase().includes('dashboard');
  const entities = requirements.data.value?.match(/Entities:\s*(.+)/)?.[1]?.split(',').map((e) => e.trim()) || ['Records'];
  const primaryEntity = entities[0] || 'Record';

  const accentColor = mode === 'simple' ? '#6366f1' : '#10b981';
  const accentHover = mode === 'simple' ? '#4f46e5' : '#059669';

  const sampleData = Array.from({ length: 5 }, (_, i) => ({
    id: i + 1,
    name: `${primaryEntity} ${i + 1}`,
    status: ['Active', 'Pending', 'Completed', 'Active', 'Pending'][i],
    date: `2026-0${i + 1}-${10 + i}`,
    value: `$${(Math.random() * 500 + 50).toFixed(2)}`,
  }));

  const tableRows = sampleData
    .map(
      (row) => `
    <tr>
      <td>${row.id}</td>
      <td>${row.name}</td>
      <td><span class="badge badge-${row.status.toLowerCase()}">${row.status}</span></td>
      <td>${row.date}</td>
      <td>${row.value}</td>
      <td>
        <button class="btn-sm" onclick="editRecord(${row.id})">Edit</button>
        <button class="btn-sm btn-danger" onclick="deleteRecord(${row.id})">Delete</button>
      </td>
    </tr>`
    )
    .join('');

  const dashboardCards = hasDashboard
    ? `
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">Total ${primaryEntity}s</div>
        <div class="stat-value">247</div>
        <div class="stat-change positive">+12% this month</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Active</div>
        <div class="stat-value">183</div>
        <div class="stat-change positive">+8% this month</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Pending</div>
        <div class="stat-value">41</div>
        <div class="stat-change neutral">No change</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Completed</div>
        <div class="stat-value">23</div>
        <div class="stat-change positive">+3 today</div>
      </div>
    </div>`
    : '';

  const authSection = hasAuth
    ? `
    <div id="auth-screen" class="auth-screen">
      <div class="auth-card">
        <h2>Sign In to ${name}</h2>
        <form onsubmit="handleLogin(event)">
          <div class="form-group">
            <label>Email</label>
            <input type="email" id="email" placeholder="you@example.com" required />
          </div>
          <div class="form-group">
            <label>Password</label>
            <input type="password" id="password" placeholder="••••••••" required />
          </div>
          <button type="submit" class="btn-primary full-width">Sign In</button>
        </form>
        <p class="auth-hint">Demo: any email + password works</p>
      </div>
    </div>`
    : '';

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${name}</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --accent: ${accentColor};
      --accent-hover: ${accentHover};
      --bg: #0f172a;
      --surface: #1e293b;
      --surface2: #334155;
      --border: #334155;
      --text: #f1f5f9;
      --muted: #94a3b8;
      --danger: #ef4444;
    }
    body { font-family: system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }
    .app-layout { display: flex; min-height: 100vh; }
    .sidebar { width: 240px; background: var(--surface); border-right: 1px solid var(--border); padding: 24px 0; flex-shrink: 0; }
    .sidebar-brand { padding: 0 20px 24px; font-size: 18px; font-weight: 700; color: var(--accent); border-bottom: 1px solid var(--border); margin-bottom: 16px; }
    .sidebar-nav { list-style: none; }
    .sidebar-nav li a { display: block; padding: 10px 20px; color: var(--muted); text-decoration: none; font-size: 14px; transition: all 0.2s; border-left: 3px solid transparent; }
    .sidebar-nav li a:hover, .sidebar-nav li a.active { color: var(--text); background: rgba(255,255,255,0.05); border-left-color: var(--accent); }
    .main-content { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
    .topbar { background: var(--surface); border-bottom: 1px solid var(--border); padding: 16px 24px; display: flex; align-items: center; justify-content: space-between; }
    .topbar h1 { font-size: 20px; font-weight: 600; }
    .topbar-actions { display: flex; gap: 12px; align-items: center; }
    .content-area { flex: 1; padding: 24px; overflow-y: auto; }
    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }
    .stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }
    .stat-label { font-size: 12px; color: var(--muted); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.05em; }
    .stat-value { font-size: 28px; font-weight: 700; margin-bottom: 4px; }
    .stat-change { font-size: 12px; }
    .stat-change.positive { color: #22c55e; }
    .stat-change.neutral { color: var(--muted); }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
    .card-header { padding: 16px 20px; border-bottom: 1px solid var(--border); display: flex; align-items: center; justify-content: space-between; }
    .card-header h2 { font-size: 16px; font-weight: 600; }
    .card-body { padding: 0; }
    table { width: 100%; border-collapse: collapse; font-size: 14px; }
    th { padding: 12px 16px; text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); border-bottom: 1px solid var(--border); background: rgba(255,255,255,0.02); }
    td { padding: 12px 16px; border-bottom: 1px solid var(--border); color: var(--text); }
    tr:last-child td { border-bottom: none; }
    tr:hover td { background: rgba(255,255,255,0.03); }
    .badge { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 600; }
    .badge-active { background: rgba(34,197,94,0.15); color: #22c55e; }
    .badge-pending { background: rgba(234,179,8,0.15); color: #eab308; }
    .badge-completed { background: rgba(99,102,241,0.15); color: #818cf8; }
    .btn-primary { background: var(--accent); color: white; border: none; padding: 10px 20px; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
    .btn-primary:hover { background: var(--accent-hover); transform: scale(1.02); }
    .btn-primary.full-width { width: 100%; }
    .btn-sm { background: transparent; border: 1px solid var(--border); color: var(--muted); padding: 4px 10px; border-radius: 6px; font-size: 12px; cursor: pointer; transition: all 0.2s; margin-right: 4px; }
    .btn-sm:hover { border-color: var(--accent); color: var(--accent); }
    .btn-danger { border-color: var(--danger); color: var(--danger); }
    .btn-danger:hover { background: rgba(239,68,68,0.1); }
    .form-group { margin-bottom: 16px; }
    .form-group label { display: block; font-size: 13px; font-weight: 500; margin-bottom: 6px; color: var(--muted); }
    .form-group input, .form-group select, .form-group textarea { width: 100%; background: var(--surface2); border: 1px solid var(--border); border-radius: 8px; padding: 10px 14px; color: var(--text); font-size: 14px; outline: none; transition: border-color 0.2s; }
    .form-group input:focus, .form-group select:focus, .form-group textarea:focus { border-color: var(--accent); }
    .modal-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 100; align-items: center; justify-content: center; }
    .modal-overlay.open { display: flex; }
    .modal { background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 28px; width: 100%; max-width: 480px; }
    .modal h3 { font-size: 18px; font-weight: 600; margin-bottom: 20px; }
    .modal-actions { display: flex; gap: 12px; justify-content: flex-end; margin-top: 20px; }
    .btn-ghost { background: transparent; border: 1px solid var(--border); color: var(--muted); padding: 10px 20px; border-radius: 8px; font-size: 14px; cursor: pointer; transition: all 0.2s; }
    .btn-ghost:hover { border-color: var(--muted); color: var(--text); }
    .auth-screen { position: fixed; inset: 0; background: var(--bg); display: flex; align-items: center; justify-content: center; z-index: 200; }
    .auth-card { background: var(--surface); border: 1px solid var(--border); border-radius: 20px; padding: 40px; width: 100%; max-width: 400px; }
    .auth-card h2 { font-size: 24px; font-weight: 700; margin-bottom: 28px; text-align: center; }
    .auth-hint { text-align: center; font-size: 12px; color: var(--muted); margin-top: 16px; }
    .toast { position: fixed; bottom: 24px; right: 24px; background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 14px 20px; font-size: 14px; z-index: 999; animation: slideIn 0.3s ease; }
    @keyframes slideIn { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
    @media (max-width: 768px) { .sidebar { display: none; } }
  </style>
</head>
<body>
  ${authSection}

  <div class="app-layout" id="app" ${hasAuth ? 'style="display:none"' : ''}>
    <aside class="sidebar">
      <div class="sidebar-brand">${name}</div>
      <ul class="sidebar-nav">
        <li><a href="#" class="active" onclick="showView('list', this)">All ${primaryEntity}s</a></li>
        ${hasDashboard ? `<li><a href="#" onclick="showView('dashboard', this)">Dashboard</a></li>` : ''}
        ${entities.slice(1).map((e) => `<li><a href="#" onclick="showView('list', this)">${e}s</a></li>`).join('')}
        <li><a href="#" onclick="showView('settings', this)">Settings</a></li>
      </ul>
    </aside>

    <div class="main-content">
      <div class="topbar">
        <h1 id="page-title">${primaryEntity}s</h1>
        <div class="topbar-actions">
          <button class="btn-primary" onclick="openModal()">+ Add ${primaryEntity}</button>
        </div>
      </div>

      <div class="content-area">
        <div id="view-dashboard" style="display:none">
          ${dashboardCards}
        </div>

        <div id="view-list">
          <div class="card">
            <div class="card-header">
              <h2>All ${primaryEntity}s</h2>
              <span id="record-count" style="font-size:13px;color:var(--muted)">5 records</span>
            </div>
            <div class="card-body">
              <table>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Name</th>
                    <th>Status</th>
                    <th>Date</th>
                    <th>Value</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody id="records-tbody">
                  ${tableRows}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div id="view-settings" style="display:none">
          <div class="card">
            <div class="card-header"><h2>Settings</h2></div>
            <div class="card-body" style="padding:24px">
              <div class="form-group">
                <label>App Name</label>
                <input type="text" value="${name}" />
              </div>
              <div class="form-group">
                <label>Default Status</label>
                <select><option>Active</option><option>Pending</option></select>
              </div>
              <button class="btn-primary" onclick="showToast('Settings saved!')">Save Settings</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="modal-overlay" id="modal">
    <div class="modal">
      <h3>Add New ${primaryEntity}</h3>
      <form onsubmit="handleAddRecord(event)">
        <div class="form-group">
          <label>Name</label>
          <input type="text" id="new-name" placeholder="${primaryEntity} name" required />
        </div>
        <div class="form-group">
          <label>Status</label>
          <select id="new-status">
            <option>Active</option>
            <option>Pending</option>
            <option>Completed</option>
          </select>
        </div>
        <div class="form-group">
          <label>Value</label>
          <input type="text" id="new-value" placeholder="$0.00" />
        </div>
        <div class="modal-actions">
          <button type="button" class="btn-ghost" onclick="closeModal()">Cancel</button>
          <button type="submit" class="btn-primary">Add ${primaryEntity}</button>
        </div>
      </form>
    </div>
  </div>

  <script>
    var records = ${JSON.stringify(sampleData)};
    var nextId = records.length + 1;

    function handleLogin(e) {
      e.preventDefault();
      document.getElementById('auth-screen').style.display = 'none';
      document.getElementById('app').style.display = 'flex';
    }

    function showView(view, el) {
      document.querySelectorAll('.sidebar-nav a').forEach(function(a) { a.classList.remove('active'); });
      if (el) el.classList.add('active');
      document.getElementById('view-list').style.display = view === 'list' ? 'block' : 'none';
      var dash = document.getElementById('view-dashboard');
      if (dash) dash.style.display = view === 'dashboard' ? 'block' : 'none';
      var settings = document.getElementById('view-settings');
      if (settings) settings.style.display = view === 'settings' ? 'block' : 'none';
      var titles = { list: '${primaryEntity}s', dashboard: 'Dashboard', settings: 'Settings' };
      document.getElementById('page-title').textContent = titles[view] || '${primaryEntity}s';
    }

    function renderTable() {
      var tbody = document.getElementById('records-tbody');
      tbody.innerHTML = records.map(function(row) {
        return '<tr><td>' + row.id + '</td><td>' + row.name + '</td><td><span class="badge badge-' + row.status.toLowerCase() + '">' + row.status + '</span></td><td>' + row.date + '</td><td>' + row.value + '</td><td><button class="btn-sm" onclick="editRecord(' + row.id + ')">Edit</button><button class="btn-sm btn-danger" onclick="deleteRecord(' + row.id + ')">Delete</button></td></tr>';
      }).join('');
      document.getElementById('record-count').textContent = records.length + ' records';
    }

    function openModal() { document.getElementById('modal').classList.add('open'); }
    function closeModal() { document.getElementById('modal').classList.remove('open'); }

    function handleAddRecord(e) {
      e.preventDefault();
      var name = document.getElementById('new-name').value;
      var status = document.getElementById('new-status').value;
      var value = document.getElementById('new-value').value || '$0.00';
      var today = new Date().toISOString().split('T')[0];
      records.push({ id: nextId++, name: name, status: status, date: today, value: value });
      renderTable();
      closeModal();
      e.target.reset();
      showToast('${primaryEntity} added successfully!');
    }

    function editRecord(id) { showToast('Edit mode for record #' + id); }

    function deleteRecord(id) {
      records = records.filter(function(r) { return r.id !== id; });
      renderTable();
      showToast('Record deleted.');
    }

    function showToast(msg) {
      var t = document.createElement('div');
      t.className = 'toast';
      t.textContent = msg;
      document.body.appendChild(t);
      setTimeout(function() { t.remove(); }, 3000);
    }

    document.getElementById('modal').addEventListener('click', function(e) {
      if (e.target === this) closeModal();
    });
  </script>
</body>
</html>`;
}