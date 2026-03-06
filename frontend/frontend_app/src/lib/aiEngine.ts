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

/* ─── Style Personalization ─── */
export type ColorSchemeId = 'ocean' | 'sunset' | 'forest' | 'royal' | 'coral' | 'slate';
export type SidebarStyle = 'gradient' | 'solid' | 'dark';
export type LayoutDensity = 'comfortable' | 'compact';

export interface ColorScheme {
  id: ColorSchemeId;
  name: string;
  primary: string;
  secondary: string;
  accent: string;
  gradient: string;
  sidebarText: string;
}

export interface StylePreferences {
  colorScheme: ColorSchemeId;
  sidebarStyle: SidebarStyle;
  density: LayoutDensity;
  brandIcon: string;
  fontStyle: 'modern' | 'classic' | 'rounded';
}

export const COLOR_SCHEMES: Record<ColorSchemeId, ColorScheme> = {
  ocean: {
    id: 'ocean',
    name: 'Ocean Blue',
    primary: '#4e73df',
    secondary: '#224abe',
    accent: '#36b9cc',
    gradient: 'linear-gradient(180deg, #4e73df 10%, #224abe 100%)',
    sidebarText: '#fff',
  },
  sunset: {
    id: 'sunset',
    name: 'Sunset',
    primary: '#e74a3b',
    secondary: '#be2617',
    accent: '#f6c23e',
    gradient: 'linear-gradient(180deg, #e74a3b 10%, #be2617 100%)',
    sidebarText: '#fff',
  },
  forest: {
    id: 'forest',
    name: 'Forest',
    primary: '#1cc88a',
    secondary: '#13855c',
    accent: '#36b9cc',
    gradient: 'linear-gradient(180deg, #1cc88a 10%, #13855c 100%)',
    sidebarText: '#fff',
  },
  royal: {
    id: 'royal',
    name: 'Royal Purple',
    primary: '#6f42c1',
    secondary: '#4e2d8e',
    accent: '#e83e8c',
    gradient: 'linear-gradient(180deg, #6f42c1 10%, #4e2d8e 100%)',
    sidebarText: '#fff',
  },
  coral: {
    id: 'coral',
    name: 'Coral',
    primary: '#fd7e14',
    secondary: '#c85a00',
    accent: '#e83e8c',
    gradient: 'linear-gradient(180deg, #fd7e14 10%, #c85a00 100%)',
    sidebarText: '#fff',
  },
  slate: {
    id: 'slate',
    name: 'Slate',
    primary: '#5a5c69',
    secondary: '#3a3b45',
    accent: '#4e73df',
    gradient: 'linear-gradient(180deg, #5a5c69 10%, #3a3b45 100%)',
    sidebarText: '#fff',
  },
};

export const BRAND_ICONS = [
  { id: 'laugh-wink', icon: 'fas fa-laugh-wink', label: 'Default' },
  { id: 'rocket', icon: 'fas fa-rocket', label: 'Rocket' },
  { id: 'bolt', icon: 'fas fa-bolt', label: 'Bolt' },
  { id: 'gem', icon: 'fas fa-gem', label: 'Gem' },
  { id: 'fire', icon: 'fas fa-fire', label: 'Fire' },
  { id: 'star', icon: 'fas fa-star', label: 'Star' },
  { id: 'heart', icon: 'fas fa-heart', label: 'Heart' },
  { id: 'crown', icon: 'fas fa-crown', label: 'Crown' },
  { id: 'leaf', icon: 'fas fa-leaf', label: 'Leaf' },
  { id: 'shield-alt', icon: 'fas fa-shield-alt', label: 'Shield' },
];

export const defaultStylePreferences = (): StylePreferences => ({
  colorScheme: 'ocean',
  sidebarStyle: 'gradient',
  density: 'comfortable',
  brandIcon: 'laugh-wink',
  fontStyle: 'modern',
});

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
  mode: 'simple' | 'expert',
  stylePrefs?: StylePreferences
): string {
  const prefs = stylePrefs || defaultStylePreferences();
  const scheme = COLOR_SCHEMES[prefs.colorScheme];
  const name = appName || 'My App';
  const hasAuth = requirements.auth.confidence > 50;
  const hasData = requirements.data.confidence > 50;
  const hasDashboard = requirements.ui.value?.toLowerCase().includes('dashboard');
  const entities = requirements.data.value?.match(/Entities:\s*(.+)/)?.[1]?.split(',').map((e) => e.trim()) || ['Records'];
  const primaryEntity = entities[0] || 'Record';

  // Domain-aware column/data definitions based on entity type
  const entityLower = primaryEntity.toLowerCase();
  type ColDef = { key: string; label: string; gen: (i: number) => string };
  let columns: ColDef[];
  if (entityLower.match(/meal|food|nutrition|calori/)) {
    columns = [
      { key: 'name', label: 'Meal', gen: (i) => ['Grilled Chicken Salad', 'Oatmeal Bowl', 'Pasta Carbonara', 'Veggie Wrap', 'Salmon Rice'][i] },
      { key: 'calories', label: 'Calories', gen: (i) => `${[420, 310, 580, 350, 490][i]}` },
      { key: 'category', label: 'Category', gen: (i) => ['Lunch', 'Breakfast', 'Dinner', 'Lunch', 'Dinner'][i] },
      { key: 'date', label: 'Date', gen: (i) => `2026-01-${10 + i}` },
    ];
  } else if (entityLower.match(/expense|budget|spending/)) {
    columns = [
      { key: 'description', label: 'Description', gen: (i) => ['Office Supplies', 'Software License', 'Travel', 'Lunch Meeting', 'Cloud Hosting'][i] },
      { key: 'amount', label: 'Amount', gen: (i) => `$${[45.99, 199.00, 320.50, 67.80, 149.99][i]}` },
      { key: 'category', label: 'Category', gen: (i) => ['Supplies', 'Software', 'Travel', 'Meals', 'Infrastructure'][i] },
      { key: 'date', label: 'Date', gen: (i) => `2026-01-${10 + i}` },
    ];
  } else if (entityLower.match(/task|todo/)) {
    columns = [
      { key: 'title', label: 'Task', gen: (i) => ['Design mockups', 'API integration', 'Write tests', 'Deploy staging', 'Code review'][i] },
      { key: 'priority', label: 'Priority', gen: (i) => ['High', 'Medium', 'High', 'Low', 'Medium'][i] },
      { key: 'assignee', label: 'Assignee', gen: (i) => ['Alice', 'Bob', 'Carol', 'Dave', 'Eve'][i] },
      { key: 'status', label: 'Status', gen: (i) => ['Active', 'Pending', 'Completed', 'Active', 'Pending'][i] },
    ];
  } else if (entityLower.match(/appointment|booking|schedule/)) {
    columns = [
      { key: 'client', label: 'Client', gen: (i) => ['John Smith', 'Jane Doe', 'Mike Chen', 'Sara Ali', 'Tom Lee'][i] },
      { key: 'service', label: 'Service', gen: (i) => ['Consultation', 'Follow-up', 'Check-up', 'Treatment', 'Consultation'][i] },
      { key: 'time', label: 'Time', gen: (i) => ['09:00 AM', '10:30 AM', '01:00 PM', '02:30 PM', '04:00 PM'][i] },
      { key: 'status', label: 'Status', gen: (i) => ['Confirmed', 'Pending', 'Completed', 'Confirmed', 'Pending'][i] },
    ];
  } else if (entityLower.match(/product|item|inventory/)) {
    columns = [
      { key: 'name', label: 'Product', gen: (i) => ['Widget A', 'Gadget B', 'Part C', 'Module D', 'Kit E'][i] },
      { key: 'sku', label: 'SKU', gen: (i) => `SKU-${1000 + i}` },
      { key: 'qty', label: 'Stock', gen: (i) => `${[150, 42, 300, 18, 85][i]}` },
      { key: 'price', label: 'Price', gen: (i) => `$${[29.99, 59.99, 12.50, 149.00, 89.95][i]}` },
    ];
  } else if (entityLower.match(/customer|client/)) {
    columns = [
      { key: 'name', label: 'Name', gen: (i) => ['John Smith', 'Jane Doe', 'Mike Chen', 'Sara Ali', 'Tom Lee'][i] },
      { key: 'email', label: 'Email', gen: (i) => [`john@example.com`, `jane@example.com`, `mike@example.com`, `sara@example.com`, `tom@example.com`][i] },
      { key: 'phone', label: 'Phone', gen: (i) => `555-010${i}` },
      { key: 'status', label: 'Status', gen: (i) => ['Active', 'Active', 'Pending', 'Active', 'Inactive'][i] },
    ];
  } else if (entityLower.match(/order/)) {
    columns = [
      { key: 'customer', label: 'Customer', gen: (i) => ['John Smith', 'Jane Doe', 'Mike Chen', 'Sara Ali', 'Tom Lee'][i] },
      { key: 'total', label: 'Total', gen: (i) => `$${[125.00, 89.50, 245.99, 67.00, 310.75][i]}` },
      { key: 'items', label: 'Items', gen: (i) => `${[3, 1, 5, 2, 4][i]}` },
      { key: 'status', label: 'Status', gen: (i) => ['Shipped', 'Processing', 'Delivered', 'Processing', 'Shipped'][i] },
    ];
  } else if (entityLower.match(/student|grade|attendance/)) {
    columns = [
      { key: 'name', label: 'Student', gen: (i) => ['Alice Johnson', 'Bob Williams', 'Carol Davis', 'David Brown', 'Eve Wilson'][i] },
      { key: 'grade', label: 'Grade', gen: (i) => ['A', 'B+', 'A-', 'B', 'A'][i] },
      { key: 'course', label: 'Course', gen: (i) => ['Math 101', 'Physics', 'Chemistry', 'English', 'History'][i] },
      { key: 'status', label: 'Status', gen: (i) => ['Enrolled', 'Enrolled', 'Enrolled', 'Probation', 'Enrolled'][i] },
    ];
  } else if (entityLower.match(/habit|workout|exercise/)) {
    columns = [
      { key: 'name', label: 'Activity', gen: (i) => ['Morning Run', 'Meditation', 'Reading', 'Gym Session', 'Journaling'][i] },
      { key: 'frequency', label: 'Frequency', gen: (i) => ['Daily', 'Daily', 'Daily', '3x/week', 'Daily'][i] },
      { key: 'streak', label: 'Streak', gen: (i) => `${[12, 30, 7, 5, 21][i]} days` },
      { key: 'status', label: 'Status', gen: (i) => ['Active', 'Active', 'Completed', 'Active', 'Pending'][i] },
    ];
  } else {
    columns = [
      { key: 'name', label: primaryEntity + ' Name', gen: (i) => `${primaryEntity} ${i + 1}` },
      { key: 'description', label: 'Description', gen: (i) => ['Initial setup', 'In progress', 'Under review', 'Approved', 'Finalized'][i] },
      { key: 'date', label: 'Date', gen: (i) => `2026-01-${10 + i}` },
      { key: 'status', label: 'Status', gen: (i) => ['Active', 'Pending', 'Completed', 'Active', 'Pending'][i] },
    ];
  }

  const sampleData = Array.from({ length: 5 }, (_, i) => {
    const row: Record<string, string | number> = { id: i + 1 };
    for (const col of columns) row[col.key] = col.gen(i);
    return row;
  });

  const statusBadge = (val: string) => {
    const s = val.toLowerCase();
    if (s.match(/active|confirmed|shipped|enrolled|delivered/)) return 'primary';
    if (s.match(/pending|processing|probation/)) return 'warning';
    if (s.match(/completed|finalized|approved/)) return 'success';
    if (s.match(/inactive|cancelled/)) return 'danger';
    return 'secondary';
  };

  const hasStatusCol = columns.some((c) => c.key === 'status');

  const tableHeaders = columns.map((c) => `<th>${c.label}</th>`).join('');
  const tableRows = sampleData
    .map((row) => {
      const cells = columns.map((c) => {
        const val = String(row[c.key]);
        if (c.key === 'status') return `<td><span class="badge badge-${statusBadge(val)}">${val}</span></td>`;
        return `<td>${val}</td>`;
      }).join('');
      return `
                    <tr>
                      <td>${row.id}</td>
                      ${cells}
                      <td>
                        <button class="btn btn-sm btn-info" onclick="editRecord(${row.id})"><i class="fas fa-edit"></i></button>
                        <button class="btn btn-sm btn-danger" onclick="deleteRecord(${row.id})"><i class="fas fa-trash"></i></button>
                      </td>
                    </tr>`;
    })
    .join('');

  // Build modal form fields from columns
  const modalFields = columns.map((c) => {
    if (c.key === 'status') {
      const opts = [...new Set(sampleData.map((r) => String(r.status)))].map((o) => `<option>${o}</option>`).join('');
      return `<div class="form-group"><label>${c.label}</label><select class="form-control" id="field-${c.key}">${opts}</select></div>`;
    }
    return `<div class="form-group"><label>${c.label}</label><input type="text" class="form-control" id="field-${c.key}" placeholder="Enter ${c.label.toLowerCase()}" required></div>`;
  }).join('\n            ');

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
    `<li class="nav-item${i === 0 ? ' active' : ''}"><a class="nav-link" href="javascript:void(0)" onclick="showView('list', this); return false;"><i class="fas fa-fw fa-table"></i><span>${e}s</span></a></li>`
  ).join('\n          ');

  // Build column keys array for JS
  const colKeys = JSON.stringify(columns.map((c) => c.key));

  // ─── Style Personalization CSS ───
  const sidebarBg = prefs.sidebarStyle === 'gradient'
    ? `background: ${scheme.gradient} !important;`
    : prefs.sidebarStyle === 'dark'
      ? `background: #1a1a2e !important;`
      : `background: ${scheme.primary} !important;`;

  const fontImport = prefs.fontStyle === 'rounded'
    ? `@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');`
    : prefs.fontStyle === 'classic'
      ? `@import url('https://fonts.googleapis.com/css2?family=Merriweather:ital,wght@0,400;0,700;1,400&family=Source+Sans+3:wght@400;600;700&display=swap');`
      : `@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');`;

  const fontFamily = prefs.fontStyle === 'rounded'
    ? `'Nunito', sans-serif`
    : prefs.fontStyle === 'classic'
      ? `'Source Sans 3', 'Merriweather', serif`
      : `'Inter', -apple-system, BlinkMacSystemFont, sans-serif`;

  const densityCss = prefs.density === 'compact'
    ? `.card-body { padding: .75rem; } .table td, .table th { padding: .4rem .75rem; } .mb-4 { margin-bottom: 1rem !important; }`
    : '';

  const brandIconClass = `fas fa-${prefs.brandIcon}`;

  const customStyleBlock = `
  <style>
    ${fontImport}
    body, .sidebar .nav-link, .sidebar-brand-text, .h1,.h2,.h3,.h4,.h5,.h6,h1,h2,h3,h4,h5,h6 {
      font-family: ${fontFamily} !important;
    }
    #accordionSidebar { ${sidebarBg} }
    .btn-primary { background-color: ${scheme.primary} !important; border-color: ${scheme.primary} !important; }
    .btn-primary:hover { background-color: ${scheme.secondary} !important; border-color: ${scheme.secondary} !important; }
    .text-primary { color: ${scheme.primary} !important; }
    .border-left-primary { border-left-color: ${scheme.primary} !important; }
    .border-left-info { border-left-color: ${scheme.accent} !important; }
    a.nav-link.active, .nav-item.active .nav-link { font-weight: 700; }
    .badge-primary { background-color: ${scheme.primary}; }
    .sidebar-brand-icon { color: ${scheme.sidebarText}; }
    .card { border-radius: .55rem; transition: box-shadow .15s ease; }
    .card:hover { box-shadow: 0 .25rem 1rem rgba(0,0,0,.12) !important; }
    .btn { border-radius: .35rem; transition: all .15s ease; }
    .btn:hover { transform: translateY(-1px); }
    ${densityCss}
  </style>`;

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
  <title>${name}</title>
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/startbootstrap-sb-admin-2@4.1.3/css/sb-admin-2.min.css" rel="stylesheet">
  <link href="https://cdn.datatables.net/1.13.4/css/dataTables.bootstrap4.min.css" rel="stylesheet">
  ${customStyleBlock}
</head>
<body id="page-top">
  ${authPage}

  <div id="wrapper"${hasAuth ? ' style="display:none"' : ''}>
    <!-- Sidebar -->
    <ul class="navbar-nav sidebar sidebar-dark accordion" id="accordionSidebar">
      <a class="sidebar-brand d-flex align-items-center justify-content-center" href="javascript:void(0)">
        <div class="sidebar-brand-icon rotate-n-15"><i class="${brandIconClass}"></i></div>
        <div class="sidebar-brand-text mx-3">${name}</div>
      </a>
      <hr class="sidebar-divider my-0">
      <li class="nav-item active"><a class="nav-link" href="javascript:void(0)" onclick="showView('dashboard', this); return false;"><i class="fas fa-fw fa-tachometer-alt"></i><span>Dashboard</span></a></li>
      <hr class="sidebar-divider">
      <div class="sidebar-heading">Management</div>
          ${sidebarNavItems}
      <li class="nav-item"><a class="nav-link" href="javascript:void(0)" onclick="showView('settings', this); return false;"><i class="fas fa-fw fa-cog"></i><span>Settings</span></a></li>
    </ul>

    <!-- Content Wrapper -->
    <div id="content-wrapper" class="d-flex flex-column">
      <div id="content">
        <!-- Topbar -->
        <nav class="navbar navbar-expand navbar-light bg-white topbar mb-4 static-top shadow">
          <button id="sidebarToggleTop" class="btn btn-link d-md-none rounded-circle mr-3"><i class="fa fa-bars"></i></button>
          <ul class="navbar-nav ml-auto">
            <li class="nav-item dropdown no-arrow">
              <a class="nav-link dropdown-toggle" href="javascript:void(0)" role="button" data-toggle="dropdown"><span class="mr-2 d-none d-lg-inline text-gray-600 small">User</span><i class="fas fa-user-circle fa-fw"></i></a>
            </li>
          </ul>
        </nav>

        <!-- Begin Page Content -->
        <div class="container-fluid">
          <div class="d-sm-flex align-items-center justify-content-between mb-4">
            <h1 class="h3 mb-0 text-gray-800" id="page-title">Dashboard</h1>
            <button class="d-none d-sm-inline-block btn btn-sm btn-primary shadow-sm" onclick="openModal()"><i class="fas fa-plus fa-sm text-white-50"></i> Add ${primaryEntity}</button>
          </div>

          <!-- Dashboard View -->
          <div id="view-dashboard">
            ${dashboardCards}
          </div>

          <!-- List View -->
          <div id="view-list">
            <div class="card shadow mb-4">
              <div class="card-header py-3 d-flex justify-content-between align-items-center">
                <h6 class="m-0 font-weight-bold text-primary">All ${primaryEntity}s</h6>
                <span class="text-muted small" id="record-count">${sampleData.length} records</span>
              </div>
              <div class="card-body">
                <div class="table-responsive">
                  <table class="table table-bordered" id="dataTable" width="100%" cellspacing="0">
                    <thead>
                      <tr>
                        <th>#</th>
                        ${tableHeaders}
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
          </div>

          <!-- Settings View -->
          <div id="view-settings" style="display:none">
            <div class="card shadow mb-4">
              <div class="card-header py-3"><h6 class="m-0 font-weight-bold text-primary">Settings</h6></div>
              <div class="card-body">
                <div class="form-group"><label>App Name</label><input type="text" class="form-control" value="${name}"></div>
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
        <div class="modal-header"><h5 class="modal-title">Add New ${primaryEntity}</h5><button type="button" class="close" data-dismiss="modal">&times;</button></div>
        <div class="modal-body">
          <form id="entityForm">
            ${modalFields}
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
    var records = ${JSON.stringify(sampleData)};
    var colKeys = ${colKeys};
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
      var titles = { list: '${primaryEntity}s', dashboard: 'Dashboard', settings: 'Settings' };
      document.getElementById('page-title').textContent = titles[view] || 'Dashboard';
      return false;
    }

    function statusBadge(val) {
      var s = (val || '').toLowerCase();
      if (s.match(/active|confirmed|shipped|enrolled|delivered/)) return 'primary';
      if (s.match(/pending|processing|probation/)) return 'warning';
      if (s.match(/completed|finalized|approved/)) return 'success';
      if (s.match(/inactive|cancelled/)) return 'danger';
      return 'secondary';
    }

    function renderTable() {
      var tbody = document.getElementById('records-tbody');
      tbody.innerHTML = records.map(function(row) {
        var cells = colKeys.map(function(k) {
          var val = row[k] || '';
          if (k === 'status') return '<td><span class="badge badge-' + statusBadge(val) + '">' + val + '</span></td>';
          return '<td>' + val + '</td>';
        }).join('');
        return '<tr><td>' + row.id + '</td>' + cells + '<td><button class="btn btn-sm btn-info" onclick="editRecord(' + row.id + ')"><i class="fas fa-edit"></i></button> <button class="btn btn-sm btn-danger" onclick="deleteRecord(' + row.id + ')"><i class="fas fa-trash"></i></button></td></tr>';
      }).join('');
      document.getElementById('record-count').textContent = records.length + ' records';
      var tc = document.getElementById('totalCount');
      if (tc) tc.textContent = records.length;
    }

    function openModal() { $('#addEditModal').modal('show'); }

    function handleAddRecord() {
      var newRec = { id: nextId++ };
      colKeys.forEach(function(k) {
        var el = document.getElementById('field-' + k);
        if (el) newRec[k] = el.value;
      });
      var today = new Date().toISOString().split('T')[0];
      if (!newRec.date) newRec.date = today;
      records.push(newRec);
      renderTable();
      $('#addEditModal').modal('hide');
      document.getElementById('entityForm').reset();
      showToast('${primaryEntity} added successfully!');
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