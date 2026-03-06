export interface RequirementsState {
  problem: { label: string; value: string | null; confidence: number };
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
  problem: { label: 'Problem / Domain', value: null, confidence: 0 },
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

  // Problem / Domain inference
  if (allText.match(/tracker|track|manage|system|app for|tool for|platform for|build a|need a|want a/)) {
    const domainHints: string[] = [];
    if (allText.match(/calori|food|meal|nutrition|diet/)) domainHints.push('nutrition/diet tracking');
    if (allText.match(/inventory|stock|warehouse/)) domainHints.push('inventory management');
    if (allText.match(/appointment|booking|schedule|salon|clinic/)) domainHints.push('appointment scheduling');
    if (allText.match(/expense|budget|spending|finance/)) domainHints.push('expense/budget tracking');
    if (allText.match(/task|todo|to-do|project/)) domainHints.push('task/project management');
    if (allText.match(/student|school|grade|attendance/)) domainHints.push('student records management');
    if (allText.match(/order|shop|store|ecommerce/)) domainHints.push('order management');
    req.problem = {
      label: 'Problem / Domain',
      value: domainHints.length > 0 ? domainHints.join(', ') : 'Custom application',
      confidence: domainHints.length > 0 ? 80 : 50,
    };
  }

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

  if (requirements.problem.confidence < 50 && count >= 1) {
    return mode === 'simple'
      ? 'Could you tell me more about what problem this app is meant to solve, and who it\'s for?'
      : 'What is the core domain and problem this system addresses?';
  }

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
                      <td><span class="badge badge-${row.status === 'Active' ? 'primary' : row.status === 'Pending' ? 'warning' : 'success'}">${row.status}</span></td>
                      <td>${row.date}</td>
                      <td>${row.value}</td>
                      <td>
                        <button class="btn btn-sm btn-info" onclick="editRecord(${row.id})"><i class="fas fa-edit"></i></button>
                        <button class="btn btn-sm btn-danger" onclick="deleteRecord(${row.id})"><i class="fas fa-trash"></i></button>
                      </td>
                    </tr>`
    )
    .join('');

  const dashboardCards = hasDashboard
    ? `
              <div class="row">
                <div class="col-xl-3 col-md-6 mb-4">
                  <div class="card border-left-primary shadow h-100 py-2">
                    <div class="card-body"><div class="row no-gutters align-items-center"><div class="col mr-2"><div class="text-xs font-weight-bold text-primary text-uppercase mb-1">Total ${primaryEntity}s</div><div class="h5 mb-0 font-weight-bold text-gray-800">247</div></div><div class="col-auto"><i class="fas fa-clipboard-list fa-2x text-gray-300"></i></div></div></div>
                  </div>
                </div>
                <div class="col-xl-3 col-md-6 mb-4">
                  <div class="card border-left-success shadow h-100 py-2">
                    <div class="card-body"><div class="row no-gutters align-items-center"><div class="col mr-2"><div class="text-xs font-weight-bold text-success text-uppercase mb-1">Active</div><div class="h5 mb-0 font-weight-bold text-gray-800">183</div></div><div class="col-auto"><i class="fas fa-check-circle fa-2x text-gray-300"></i></div></div></div>
                  </div>
                </div>
                <div class="col-xl-3 col-md-6 mb-4">
                  <div class="card border-left-warning shadow h-100 py-2">
                    <div class="card-body"><div class="row no-gutters align-items-center"><div class="col mr-2"><div class="text-xs font-weight-bold text-warning text-uppercase mb-1">Pending</div><div class="h5 mb-0 font-weight-bold text-gray-800">41</div></div><div class="col-auto"><i class="fas fa-clock fa-2x text-gray-300"></i></div></div></div>
                  </div>
                </div>
                <div class="col-xl-3 col-md-6 mb-4">
                  <div class="card border-left-info shadow h-100 py-2">
                    <div class="card-body"><div class="row no-gutters align-items-center"><div class="col mr-2"><div class="text-xs font-weight-bold text-info text-uppercase mb-1">Completed</div><div class="h5 mb-0 font-weight-bold text-gray-800">23</div></div><div class="col-auto"><i class="fas fa-flag-checkered fa-2x text-gray-300"></i></div></div></div>
                  </div>
                </div>
              </div>`
    : `
              <div class="row">
                <div class="col-xl-3 col-md-6 mb-4">
                  <div class="card border-left-primary shadow h-100 py-2">
                    <div class="card-body"><div class="row no-gutters align-items-center"><div class="col mr-2"><div class="text-xs font-weight-bold text-primary text-uppercase mb-1">Total</div><div class="h5 mb-0 font-weight-bold text-gray-800" id="totalCount">5</div></div><div class="col-auto"><i class="fas fa-calendar fa-2x text-gray-300"></i></div></div></div>
                  </div>
                </div>
              </div>`;

  const authPage = hasAuth
    ? `
  <div id="auth-screen" style="position:fixed;inset:0;background:#f8f9fc;display:flex;align-items:center;justify-content:center;z-index:9999;">
    <div class="card shadow" style="width:400px;">
      <div class="card-body p-5">
        <div class="text-center mb-4"><h1 class="h4 text-gray-900">Sign In to ${name}</h1></div>
        <form onsubmit="handleLogin(event)">
          <div class="form-group"><input type="email" class="form-control form-control-user" id="email" placeholder="Email Address" required></div>
          <div class="form-group"><input type="password" class="form-control form-control-user" id="password" placeholder="Password" required></div>
          <button type="submit" class="btn btn-primary btn-user btn-block">Login</button>
        </form>
        <hr><div class="text-center"><small class="text-muted">Demo: any email + password works</small></div>
      </div>
    </div>
  </div>`
    : '';

  const sidebarNavItems = entities.map((e, i) =>
    `<li class="nav-item${i === 0 ? ' active' : ''}"><a class="nav-link" href="#" onclick="showView('list', this)"><i class="fas fa-fw fa-table"></i><span>${e}s</span></a></li>`
  ).join('\n          ');

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
  <title>\${name}</title>
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/startbootstrap-sb-admin-2@4.1.3/css/sb-admin-2.min.css" rel="stylesheet">
  <link href="https://cdn.datatables.net/1.13.4/css/dataTables.bootstrap4.min.css" rel="stylesheet">
</head>
<body id="page-top">
  \${authPage}

  <div id="wrapper"\${hasAuth ? ' style="display:none"' : ''}>
    <!-- Sidebar -->
    <ul class="navbar-nav bg-gradient-primary sidebar sidebar-dark accordion" id="accordionSidebar">
      <a class="sidebar-brand d-flex align-items-center justify-content-center" href="#">
        <div class="sidebar-brand-icon rotate-n-15"><i class="fas fa-laugh-wink"></i></div>
        <div class="sidebar-brand-text mx-3">\${name}</div>
      </a>
      <hr class="sidebar-divider my-0">
      <li class="nav-item active"><a class="nav-link" href="#" onclick="showView('dashboard', this)"><i class="fas fa-fw fa-tachometer-alt"></i><span>Dashboard</span></a></li>
      <hr class="sidebar-divider">
      <div class="sidebar-heading">Management</div>
          \${sidebarNavItems}
      <li class="nav-item"><a class="nav-link" href="#" onclick="showView('settings', this)"><i class="fas fa-fw fa-cog"></i><span>Settings</span></a></li>
    </ul>

    <!-- Content Wrapper -->
    <div id="content-wrapper" class="d-flex flex-column">
      <div id="content">
        <!-- Topbar -->
        <nav class="navbar navbar-expand navbar-light bg-white topbar mb-4 static-top shadow">
          <button id="sidebarToggleTop" class="btn btn-link d-md-none rounded-circle mr-3"><i class="fa fa-bars"></i></button>
          <ul class="navbar-nav ml-auto">
            <li class="nav-item dropdown no-arrow">
              <a class="nav-link dropdown-toggle" href="#" role="button" data-toggle="dropdown"><span class="mr-2 d-none d-lg-inline text-gray-600 small">User</span><i class="fas fa-user-circle fa-fw"></i></a>
            </li>
          </ul>
        </nav>

        <!-- Begin Page Content -->
        <div class="container-fluid">
          <div class="d-sm-flex align-items-center justify-content-between mb-4">
            <h1 class="h3 mb-0 text-gray-800" id="page-title">Dashboard</h1>
            <button class="d-none d-sm-inline-block btn btn-sm btn-primary shadow-sm" onclick="openModal()"><i class="fas fa-plus fa-sm text-white-50"></i> Add \${primaryEntity}</button>
          </div>

          <!-- Dashboard View -->
          <div id="view-dashboard">
            \${dashboardCards}
          </div>

          <!-- List View -->
          <div id="view-list">
            <div class="card shadow mb-4">
              <div class="card-header py-3 d-flex justify-content-between align-items-center">
                <h6 class="m-0 font-weight-bold text-primary">All \${primaryEntity}s</h6>
                <span class="text-muted small" id="record-count">\${sampleData.length} records</span>
              </div>
              <div class="card-body">
                <div class="table-responsive">
                  <table class="table table-bordered" id="dataTable" width="100%" cellspacing="0">
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
                    \${tableRows}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>

          <!-- Settings View -->
          <div id="view-settings" style="display:none">
            <div class="card shadow mb-4">
              <div class="card-header py-3"><h6 class="m-0 font-weight-bold text-primary">Settings</h6></div>
              <div class="card-body">
                <div class="form-group"><label>App Name</label><input type="text" class="form-control" value="\${name}"></div>
                <div class="form-group"><label>Default Status</label><select class="form-control"><option>Active</option><option>Pending</option></select></div>
                <button class="btn btn-primary" onclick="showToast('Settings saved!')">Save Settings</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <footer class="sticky-footer bg-white">
        <div class="container my-auto"><div class="copyright text-center my-auto"><span>AppForge AI &copy; 2026</span></div></div>
      </footer>
    </div>
  </div>

  <!-- Add/Edit Modal -->
  <div class="modal fade" id="addEditModal" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header"><h5 class="modal-title">Add New \${primaryEntity}</h5><button type="button" class="close" data-dismiss="modal">&times;</button></div>
        <div class="modal-body">
          <form id="entityForm">
            <div class="form-group"><label>Name</label><input type="text" class="form-control" id="new-name" placeholder="\${primaryEntity} name" required></div>
            <div class="form-group"><label>Status</label><select class="form-control" id="new-status"><option>Active</option><option>Pending</option><option>Completed</option></select></div>
            <div class="form-group"><label>Value</label><input type="text" class="form-control" id="new-value" placeholder="$0.00"></div>
          </form>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" data-dismiss="modal">Cancel</button>
          <button class="btn btn-primary" onclick="handleAddRecord()">Save</button>
        </div>
      </div>
    </div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/jquery@3.6.0/dist/jquery.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/jquery.easing@1.4.1/jquery.easing.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/startbootstrap-sb-admin-2@4.1.3/js/sb-admin-2.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@2.9.4/dist/Chart.min.js"></script>
  <script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js"></script>
  <script src="https://cdn.datatables.net/1.13.4/js/dataTables.bootstrap4.min.js"></script>
  <script>
    var records = \${JSON.stringify(sampleData)};
    var nextId = records.length + 1;

    function handleLogin(e) {
      e.preventDefault();
      document.getElementById('auth-screen').style.display = 'none';
      document.getElementById('wrapper').style.display = '';
    }

    function showView(view, el) {
      document.querySelectorAll('#accordionSidebar .nav-item').forEach(function(li) { li.classList.remove('active'); });
      if (el) el.closest('.nav-item').classList.add('active');
      document.getElementById('view-dashboard').style.display = view === 'dashboard' ? 'block' : 'none';
      document.getElementById('view-list').style.display = view === 'list' ? 'block' : 'none';
      document.getElementById('view-settings').style.display = view === 'settings' ? 'block' : 'none';
      var titles = { list: '\${primaryEntity}s', dashboard: 'Dashboard', settings: 'Settings' };
      document.getElementById('page-title').textContent = titles[view] || 'Dashboard';
    }

    function renderTable() {
      var tbody = document.getElementById('records-tbody');
      tbody.innerHTML = records.map(function(row) {
        var badgeClass = row.status === 'Active' ? 'primary' : row.status === 'Pending' ? 'warning' : 'success';
        return '<tr><td>' + row.id + '</td><td>' + row.name + '</td><td><span class="badge badge-' + badgeClass + '">' + row.status + '</span></td><td>' + row.date + '</td><td>' + row.value + '</td><td><button class="btn btn-sm btn-info" onclick="editRecord(' + row.id + ')"><i class="fas fa-edit"></i></button> <button class="btn btn-sm btn-danger" onclick="deleteRecord(' + row.id + ')"><i class="fas fa-trash"></i></button></td></tr>';
      }).join('');
      document.getElementById('record-count').textContent = records.length + ' records';
      var tc = document.getElementById('totalCount');
      if (tc) tc.textContent = records.length;
    }

    function openModal() { $('#addEditModal').modal('show'); }

    function handleAddRecord() {
      var n = document.getElementById('new-name').value;
      var s = document.getElementById('new-status').value;
      var v = document.getElementById('new-value').value || '$0.00';
      var today = new Date().toISOString().split('T')[0];
      records.push({ id: nextId++, name: n, status: s, date: today, value: v });
      renderTable();
      $('#addEditModal').modal('hide');
      document.getElementById('entityForm').reset();
      showToast('\${primaryEntity} added successfully!');
    }

    function editRecord(id) { showToast('Edit mode for record #' + id); }

    function deleteRecord(id) {
      records = records.filter(function(r) { return r.id !== id; });
      renderTable();
      showToast('Record deleted.');
    }

    function showToast(msg) {
      var t = $('<div class="alert alert-success alert-dismissible fade show" style="position:fixed;bottom:24px;right:24px;z-index:9999;min-width:250px;">' + msg + '<button type="button" class="close" data-dismiss="alert">&times;</button></div>');
      $('body').append(t);
      setTimeout(function() { t.alert('close'); }, 3000);
    }

    $(document).ready(function() {
      if ($.fn.DataTable) { $('#dataTable').DataTable(); }
    });
  </script>
</body>
</html>`;
}