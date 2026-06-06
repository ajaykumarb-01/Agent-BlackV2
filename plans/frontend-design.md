# Frontend Design — Multi-Agent Research Ecosystem (ChatGPT-like UI)

> **Style:** Monochrome (black & white) with auto light/dark mode, ChatGPT-like conversational interface  
> **Framework:** React (Vite + TypeScript)  
> **Key Dependencies:** `mermaid`, `react-router-dom`, `zustand`, `react-markdown`

---

## 1. Layout Structure (ChatGPT-style)

```
┌─────────────────────────────────────────────────────┐
│  Header (sticky, thin)                              │
│  [☰]  [Agent Research Ecosystem]  [⚫ online]  [🌙] │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Main Content Area (scrollable, centered, max 860px)│
│                                                     │
│  ┌─────────────────────────────────────────────┐    │
│  │  System Status Bar (collapsible)            │    │
│  │  ● CV Agent  ● NLP Agent  ● ML Agent       │    │
│  │  Selected: [auto]  |  Provider: Gemini      │    │
│  └─────────────────────────────────────────────┘    │
│                                                     │
│  ┌─────────────────────────────────────────────┐    │
│  │  Conversation Thread                         │    │
│  │                                             │    │
│  │  ┌─ User Message ──────────────────────┐   │    │
│  │  │ Build an OCR solution...            │   │    │
│  │  └─────────────────────────────────────┘   │    │
│  │                                             │    │
│  │  ┌─ Assistant Response ────────────────┐   │    │
│  │  │ [View Report] [Diagram] [Raw] [Copy]│   │    │
│  │  │ Agents used: CV + ML                │   │    │
│  │  │ ┌─ Literature Review ──────────────┐│   │    │
│  │  │ │ (collapsible, markdown rendered) ││   │    │
│  │  │ └──────────────────────────────────┘│   │    │
│  │  │ ┌─ Datasets ───────────────────────┐│   │    │
│  │  │ │ (collapsible)                    ││   │    │
│  │  │ └──────────────────────────────────┘│   │    │
│  │  │ ┌─ Models ─────────────────────────┐│   │    │
│  │  │ │ (collapsible)                    ││   │    │
│  │  │ └──────────────────────────────────┘│   │    │
│  │  │ ┌─ Evaluation Plan ────────────────┐│   │    │
│  │  │ │ (collapsible)                    ││   │    │
│  │  │ └──────────────────────────────────┘│   │    │
│  │  │ ┌─ Prototype Guidance ─────────────┐│   │    │
│  │  │ │ (collapsible, code blocks)       ││   │    │
│  │  │ └──────────────────────────────────┘│   │    │
│  │  └─────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────┘    │
│                                                     │
│  ┌─────────────────────────────────────────────┐    │
│  │  Input Area (sticky bottom)                  │    │
│  │  ┌──────────────────────────┐ [⚙] [Send] │    │
│  │  │ Type your research query │               │    │
│  │  └──────────────────────────┘               │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

### Side Navigation (drawer, opens on ☰)
- **Dashboard** — System overview, live agent status indicators
- **History** — Past queries and responses
- **Agents** — Agent management, logs, MCP tools, capabilities, A2A cards
- **Settings** — LLM provider config, tech stack, agent URLs
- **Diagram** — Full-page Mermaid flow visualizations

---

## 2. Color System

### Mode Detection
- Auto-detect `prefers-color-scheme` via `matchMedia`
- Manual toggle in header (sun/moon icon, always visible)
- Persist choice in `localStorage`

### Light Mode Palette
| Role | Hex | Usage |
|------|-----|-------|
| Background | `#FFFFFF` | Main page bg |
| Surface | `#F5F5F5` | Cards, sidebars, modals, message bubbles |
| Surface Hover | `#EBEBEB` | Hover states |
| Border | `#D4D4D4` | Card borders, dividers, input borders |
| Border Light | `#E5E5E5` | Subtle dividers |
| Text Primary | `#1A1A1A` | Headings, body |
| Text Secondary | `#666666` | Labels, captions |
| Text Muted | `#999999` | Placeholder, disabled |
| User Bubble | `#1A1A1A` | User message background |
| User Text | `#FFFFFF` | User message text |

### Dark Mode Palette
| Role | Hex | Usage |
|------|-----|-------|
| Background | `#0A0A0A` | Main page bg |
| Surface | `#1A1A1A` | Cards, sidebars, modals |
| Surface Hover | `#262626` | Hover states |
| Border | `#333333` | Card borders, dividers |
| Text Primary | `#F0F0F0` | Headings, body |
| Text Secondary | `#999999` | Labels, captions |
| Text Muted | `#555555` | Placeholder, disabled |
| User Bubble | `#F0F0F0` | User message background |
| User Text | `#0A0A0A` | User message text |

### Accent — Status & Alerts (shared across modes)
| Role | Hex |
|------|-----|
| Success | `#22C55E` |
| Error | `#EF4444` |
| Warning | `#F59E0B` |
| Info | `#3B82F6` |

---

## 3. Conversation Components

### 3.1 Message Bubbles
- **User**: Dark bubble (light mode) / Light bubble (dark mode), right-aligned, rounded corners
- **Assistant**: Surface background, left-aligned, monochrome styled
- Each assistant response includes an **agents-used badge**: "CV + ML" showing which agents were selected by the orchestrator for that query
- Toolbar: [View Report] [Diagram] [Raw JSON] [Copy]
- Loading state: Animated pulse dots while waiting for response

### 3.2 Report View (inside assistant message, collapsible sections)
- **Sections**: Literature Review, Datasets, Models, Evaluation Plan, Prototype Guidance
- Each section is a collapsible card with monochrome styling
- Content rendered with react-markdown for rich formatting (code blocks, tables, lists)
- If a section is empty/null from the API, show "Not applicable for this query" muted text

### 3.3 Mermaid Diagram (inside assistant message or full-page)
- Rendered inline via `mermaid.render()`
- SVG inherits theme colors
- **Glow effects via CSS filters**:
  - Yellow: `filter: drop-shadow(0 0 8px rgba(245, 158, 11, 0.7))`
  - Orange: `filter: drop-shadow(0 0 8px rgba(249, 115, 22, 0.7))`
  - Blue: `filter: drop-shadow(0 0 8px rgba(59, 130, 246, 0.7))`
  - Red: `filter: drop-shadow(0 0 8px rgba(239, 68, 68, 0.7))`
  - Green: `filter: drop-shadow(0 0 6px rgba(34, 197, 94, 0.7))`

### 3.4 Raw JSON View
- Monospace, syntax-highlighted JSON viewer
- Shows the full orchestrated response from the backend
- Collapsible by default

### 3.5 Input Area
- Single textarea (auto-resizing, 1-6 lines)
- "Send" button (prominent, right-aligned)
- Settings gear icon (opens tech stack preferences modal)
- Submit on Enter, Shift+Enter for newline

---

## 4. Page-by-Page Design

### 4.1 Dashboard (/)
- System Status Bar (pinned at top of content area)
  - 3 agent status dots (green/red) with names
  - **Agent auto-selection indicator**: shows whether orchestrator is actively selecting agents per query
  - LLM provider badge (Gemini / OpenAI / Anthropic)
  - Uptime counter
- Quick Stats row: Total Queries, Active Agents, Uptime, Avg Response Time
- Recent activity list (last 5 queries with timestamps and agents-used badges)
- "New Query" button → navigates to /chat
- **Tools Summary**: total tools registered across all agents (39 total, 13 per agent)

### 4.2 Chat (/chat) — Primary Interface
- Full conversation view (ChatGPT-style)
- Scrollable message thread
- Sticky input at bottom
- Messages stored in zustand store (persisted to localStorage)
- Each message has:
  - Role indicator (User / Assistant)
  - Timestamp
  - **Agents-used badge** (e.g., "CV + ML")
  - Content (markdown rendered)
  - Collapsible sections for structured data (literature_review, datasets, models, evaluation_plan, prototype_guidance)
  - Diagram toggle button
  - Raw JSON toggle button
  - Copy button

### 4.3 History (/history)
- List of all past queries (grouped by date)
- Search bar to filter history
- Click to reload conversation in chat view
- Delete individual items
- Shows agents-used badge per query

### 4.4 Agents (/agents)
- 3 agent cards in a responsive grid
- Each card shows:
  - Agent name + status dot
  - Port (8001/8002/8003), uptime
  - Description from A2A Agent Card
  - **13 tools** listed with monochrome tags (expandable, grouped by category: Research, Analysis, Solutioning, Prototype)
  - MCP tools list (expandable JSON)
  - A2A Agent Card viewer (expandable, shows proper description now)
  - Capabilities endpoint viewer
  - Logs viewer (monospace, tail)
- Global controls: "Start All" / "Stop All"
- Auto-discovery: calls `/api/agents/discover` on mount

### 4.5 Settings (/settings)
- **LLM Provider**: Dropdown (gemini/openai/anthropic) + model input + API key (password) + Test Connection button
- **Agent URLs**: 3 inputs (research/solution/experiment) with default reset buttons
- **Tech Stack**: Editable key-value pairs with "Add Row" button
- **Theme**: Light/Dark/System toggle

### 4.6 Diagram (/diagram)
- Full-page Mermaid viewer
- Tab selector: Agent Flow / Tech Stack / Custom
- Zoom controls (floating bottom-right)
- Download: PNG, SVG

---

## 5. API Interaction

All API calls go to the FastAPI backend at `http://localhost:8080/api`.

### Endpoints to consume
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/status` | GET | System + agent status |
| `/api/query` | POST | Submit research query → host-agent orchestrates |
| `/api/query/history` | GET | Recent queries |
| `/api/settings` | GET | Current config |
| `/api/settings` | PUT | Update config |
| `/api/agents/start` | POST | Start all agent services |
| `/api/agents/stop` | POST | Stop all agent services |
| `/api/agents/{name}/logs` | GET | Agent log tail |
| `/api/agents/discover` | GET | Discover all agent capabilities (auto-discovery) |
| `/api/agents/{name}/card` | GET | A2A agent card for specific agent |
| `/api/tech-stack` | GET | Tech stack prefs |
| `/api/tech-stack` | PUT | Update tech stack |
| `/api/diagram/agent-flow` | POST | Generate A2A flow diagram (Mermaid) |
| `/api/diagram/tech-stack` | POST | Generate tech stack diagram (Mermaid) |

### Query Response Shape
The POST `/api/query` response returns an orchestrated result with these keys:
```json
{
  "result": {
    "literature_review": "markdown text or null",
    "datasets": "markdown text or null",
    "models": "markdown text or null",
    "evaluation_plan": "markdown text or null",
    "prototype_guidance": "markdown text or null"
  },
  "agents_used": ["research", "solution"],
  "reasoning": "Agent selection rationale"
}
```

### Zustand Store Shape
```typescript
interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
  sections?: {
    literature_review?: string;
    datasets?: string;
    models?: string;
    evaluation_plan?: string;
    prototype_guidance?: string;
  };
  agentsUsed?: string[];
  reasoning?: string;
}

interface AppStore {
  messages: Message[];
  addMessage: (msg: Message) => void;
  updateLastMessage: (partial: Partial<Message>) => void;
  clearMessages: () => void;
  status: SystemStatus | null;
  setStatus: (s: SystemStatus) => void;
  darkMode: boolean;
  toggleDarkMode: () => void;
  settings: SettingsResponse | null;
  setSettings: (s: SettingsResponse) => void;
}
```

---

## 6. Component Tree

```
App
├── Layout
│   ├── Header
│   │   ├── MenuButton
│   │   ├── Logo
│   │   ├── StatusIndicator
│   │   └── DarkModeToggle
│   ├── SideDrawer (overlay)
│   │   └── NavItems (Dashboard, Chat, History, Agents, Diagram, Settings)
│   └── MainContent (router outlet)
│
├── Pages
│   ├── DashboardPage
│   │   ├── StatusBar
│   │   │   ├── AgentStatusDot (x3)
│   │   │   ├── AgentSelectionIndicator
│   │   │   └── ProviderBadge
│   │   ├── QuickStats
│   │   │   ├── TotalQueries
│   │   │   ├── ActiveAgents
│   │   │   ├── Uptime
│   │   │   └── AvgResponseTime
│   │   ├── RecentActivity
│   │   │   └── ActivityItem (query + agents-used badge + timestamp)
│   │   └── ToolsSummary (39 tools across 3 agents)
│   │
│   ├── ChatPage
│   │   ├── MessageThread
│   │   │   └── MessageBubble (xN)
│   │   │       ├── AgentsUsedBadge
│   │   │       ├── ReportSection (literature_review, datasets, models, eval, prototype)
│   │   │       ├── MermaidSection
│   │   │       ├── RawJsonViewer
│   │   │       └── ActionToolbar (View Report / Diagram / Raw JSON / Copy)
│   │   └── InputArea
│   │       ├── TechStackModal
│   │       └── SendButton
│   │
│   ├── HistoryPage
│   │   ├── SearchBar
│   │   └── HistoryList
│   │       └── HistoryItem (query + agents-used badge + date + delete)
│   │
│   ├── AgentsPage
│   │   ├── AgentControls ("Start All" / "Stop All")
│   │   └── AgentCardGrid
│   │       └── AgentCard
│   │           ├── StatusDot + AgentName
│   │           ├── Description + Port + Uptime
│   │           ├── CapabilityTags (monochrome, 13 per agent)
│   │           ├── McpToolsList (expandable JSON)
│   │           ├── AgentCardViewer (expandable, from A2A)
│   │           ├── CapabilitiesViewer
│   │           └── LogViewer (monospace, tail)
│   │
│   ├── DiagramPage
│   │   ├── DiagramTypeSelector (Agent Flow / Tech Stack / Custom)
│   │   ├── MermaidViewer (full-page)
│   │   └── ExportControls (PNG / SVG)
│   │
│   └── SettingsPage
│       ├── LLMProviderSection (dropdown + model + key + test)
│       ├── AgentUrlsSection (3 inputs + reset)
│       └── TechStackSection (key-value editor + add row)
│
└── Shared Components
    ├── Card
    ├── Button
    ├── TextInput
    ├── Toggle
    ├── StatusDot
    ├── Tag / Chip
    ├── CollapsibleSection
    ├── LoadingDots
    ├── Modal
    ├── AgentsUsedBadge (e.g., "CV + ML")
    └── RawJsonViewer (monospace, syntax-highlighted)
```

---

## 7. Mermaid Styling

### Implementation
```tsx
import mermaid from 'mermaid';

mermaid.initialize({
  theme: 'base',
  themeVariables: {
    background: 'transparent',
    primaryColor: mode === 'dark' ? '#1A1A1A' : '#F5F5F5',
    primaryTextColor: mode === 'dark' ? '#F0F0F0' : '#1A1A1A',
    lineColor: mode === 'dark' ? '#555' : '#999',
    secondaryColor: mode === 'dark' ? '#262626' : '#EBEBEB',
    tertiaryColor: mode === 'dark' ? '#333' : '#D4D4D4',
  }
});
```

### SVG Glow Filters
```css
.edge-glow-yellow { filter: drop-shadow(0 0 8px rgba(245, 158, 11, 0.7)); }
.edge-glow-orange { filter: drop-shadow(0 0 8px rgba(249, 115, 22, 0.7)); }
.edge-glow-blue   { filter: drop-shadow(0 0 8px rgba(59, 130, 246, 0.7)); }
.edge-glow-red    { filter: drop-shadow(0 0 8px rgba(239, 68, 68, 0.7)); }
.edge-glow-green  { filter: drop-shadow(0 0 6px rgba(34, 197, 94, 0.7)); }
```

---

## 8. Responsive Behavior

| Breakpoint | Layout |
|------------|--------|
| >1200px | Side drawer available, 860px centered content, 3-column agent cards |
| 768-1200px | Full-width content, drawer overlay, 2-column agent cards |
| <768px | Full-width, bottom input, compact header, 1-column agent cards |

---

## 9. File Structure

```
src/
├── components/
│   ├── layout/
│   │   ├── Header.tsx
│   │   ├── SideDrawer.tsx
│   │   └── Layout.tsx
│   ├── chat/
│   │   ├── MessageBubble.tsx
│   │   ├── MessageThread.tsx
│   │   ├── InputArea.tsx
│   │   ├── ReportSection.tsx
│   │   ├── AgentsUsedBadge.tsx
│   │   └── RawJsonViewer.tsx
│   ├── shared/
│   │   ├── Card.tsx
│   │   ├── Button.tsx
│   │   ├── TextInput.tsx
│   │   ├── Toggle.tsx
│   │   ├── StatusDot.tsx
│   │   ├── Tag.tsx
│   │   ├── Collapsible.tsx
│   │   ├── LoadingDots.tsx
│   │   └── Modal.tsx
│   └── mermaid/
│       ├── MermaidRenderer.tsx
│       └── ZoomControls.tsx
├── pages/
│   ├── Dashboard.tsx
│   ├── Chat.tsx
│   ├── History.tsx
│   ├── Agents.tsx
│   ├── Diagram.tsx
│   └── Settings.tsx
├── store/
│   └── useStore.ts
├── api/
│   └── client.ts
├── hooks/
│   ├── useDarkMode.ts
│   └── useMermaid.ts
├── types/
│   └── index.ts
├── styles/
│   ├── globals.css
│   ├── variables.css
│   └── mermaid.css
├── App.tsx
└── main.tsx
```
