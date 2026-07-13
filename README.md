# DEBRIEF— HCP Interaction Module

An AI-first "Log Interaction Screen" for a pharmaceutical CRM, built for field reps to log
Healthcare Professional (HCP) touchpoints via **either** a structured form **or** a
conversational AI agent — built on **React + Redux**, **FastAPI**, **LangGraph**, and **Groq**
(`llama-3.3-70b-versatile` — the brief's mandated `gemma2-9b-it` has since been decommissioned by
Groq; see [§4](#4-langgraph-agent--tools)).
— "AI-First CRM HCP Module: Log Interaction


---

## 1. What this is

The Log Interaction screen is a **split screen**: the **Interaction Details form on the left**, and
an **AI assistant chat on the right**. The rep never types into the form — they describe the visit
to the assistant the way they'd tell a colleague — *"Just saw Dr. Mehta, discussed Cardivax, she
was positive and wants samples next time"* — and the LangGraph agent **fills the form on the left**
for them: it extracts interaction type, products, samples, materials and follow-up, and infers a
summary and sentiment. If something's wrong, the rep corrects it in chat — *"actually it was a
call, and the sentiment was negative"* — and the agent updates **only those fields**, leaving the
rest as they were. The rep reviews the filled form and clicks **Log Interaction** to save it to the
database. This is the video's core requirement: the AI drives the form; the form is not filled by
hand.

**Two entry modes, one data model:**

| | Structured Form | Conversational Chat |
|---|---|---|
| Input | Typed fields (type, date, time, attendees, products, samples, materials, outcomes, sentiment) | Natural language |
| Enrichment | LLM summarizes `topics_discussed` → `summary`; infers sentiment unless set manually | Agent extracts *every* field itself via tool-call arguments |
| Who calls the LLM | `POST /api/interactions` route, directly | The LangGraph agent, via the `log_interaction` tool |

---

## 2. Quick start

### Option A — local dev, fastest path (SQLite, no Docker)

```bash
# Backend
cd backend
python3 -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: paste your GROQ_API_KEY (see step 3 below). DATABASE_URL can stay unset — it
# defaults to a local SQLite file so you can run this without Postgres installed.
python -m app.seed          # creates tables + demo HCPs
uvicorn app.main:app --reload --port 8000
```

```bash
# Frontend, in a second terminal
cd frontend
npm install
cp .env.example .env        # defaults to http://localhost:8000/api — fine for local dev
npm run dev
```

Open **http://localhost:5173**. The API docs are at **http://localhost:8000/docs**.

### Option B — Docker Compose (Postgres, matches the spec exactly)

```bash
cp backend/.env.example backend/.env   # then paste your GROQ_API_KEY into backend/.env
docker compose up --build
```

This starts Postgres, the FastAPI backend (seeded automatically on boot), and the frontend
(served via nginx) at **http://localhost:5173**.

### Step 3 — Get a Groq API key

Create a free key at **https://console.groq.com/keys** and paste it into `GROQ_API_KEY` in
`backend/.env`. Without a key, the app still runs — the structured form and interaction history
work normally, and the chat endpoint replies with a clear "add your API key" message instead of
crashing — but the agent can't actually call the LLM.

---

## 3. Tech stack (per the brief)

| Requirement | Implementation |
|---|---|
| Structured form **and** conversational chat | Split screen: `StructuredForm.jsx` (AI-filled, left) beside `ChatPanel.jsx` (assistant, right) in `LogInteractionScreen.jsx`. The chat fills/edits the form via the log/edit tools; the rep saves it. |
| React + Redux | Vite + React 18, Redux Toolkit (`hcpSlice`, `interactionsSlice`, `chatSlice`) |
| Python + FastAPI | `backend/app/main.py` + routers under `app/api/` |
| AI agent framework: LangGraph | `backend/app/agents/graph.py` — explicit `StateGraph`, not the `create_react_agent` shortcut, so the orchestration is visible |
| Groq LLM (mandated `gemma2-9b-it`, **now decommissioned** — see [§4](#4-langgraph-agent--tools)) | Runs on `llama-3.3-70b-versatile`, the substitute the brief explicitly permits; drives the agent's tool-routing loop (`app/agents/llm.py`) |
| Groq `llama-3.3-70b-versatile` "for context" | Also used for the `hcp_insights` tool, which summarizes/reasons over an HCP's *entire* interaction history |
| Database: MySQL/Postgres | PostgreSQL via SQLAlchemy async + `asyncpg` (`docker-compose.yml`); falls back to SQLite for zero-setup local dev — see `app/core/config.py` |
| Font: Google Inter | Loaded in `frontend/index.html`, set as the base font in `styles/index.css` |

---

## 4. The LangGraph agent

### Role

The agent is the CRM's data-entry layer for the conversational path. Reps talk to it the way
they'd talk to a colleague after a visit; the agent is responsible for (a) figuring out *which*
CRM operation that maps to, (b) extracting the structured fields an operation needs from free
text, and (c) calling the right tool(s) — possibly several in sequence (e.g. look up history,
*then* log a new visit informed by it) — before replying in plain language. It is **not** just a
chatbot bolted onto the CRM; it's the mechanism by which unstructured rep narration becomes
structured, queryable CRM data.

### Orchestration

`app/agents/graph.py` builds a classic ReAct-style loop explicitly with `StateGraph`:

```
        ┌────────────┐   tool_calls present   ┌───────────┐
   ───▶ │   agent    │ ─────────────────────▶ │   tools   │
        │ (gemma2-9b │                         │ (ToolNode)│
        │  -it, LLM) │ ◀───────────────────── │           │
        └─────┬──────┘      tool results        └───────────┘
              │
              │ no tool_calls
              ▼
             END
```

* **`agent` node** — the LLM (bound to all 5 tools via `bind_tools`) reads the conversation and
  either calls a tool or produces a final reply.
* **`tools` node** — a LangGraph `ToolNode` executes whichever tool(s) were requested and appends
  the results as `ToolMessage`s, then hands control back to `agent` — which can react to what it
  learned (e.g. call `search_interactions`, then `log_interaction` with the richer context).
* A `MemorySaver` checkpointer keys state by `session_id` (LangGraph's `thread_id`), so a chat has
  continuity ("no, make it Tuesday not Wednesday") within a session.

See `docs/ARCHITECTURE.md` for the full request-to-response sequence diagram, including how the
FastAPI layer, the graph, and the database fit together.

### The 5 tools (`app/agents/tools/`)

1. **`log_interaction`** *(mandatory)* — **fills the left-hand form** from the rep's description.
   The agent extracts the arguments (type, products, samples, materials, follow-up) from the free
   text itself before calling this tool; the tool then makes two further focused LLM calls of its
   own — summarization (`SUMMARY_EXTRACTION_PROMPT`) and sentiment classification
   (`SENTIMENT_PROMPT`) — so *what* gets extracted and *how it's written up* are both LLM-driven,
   per the brief's "potentially using the LLM for summarization, entity extraction" note. It
   **stages** the fields into the form (returns a `draft`); it does not save — the rep clicks
   **Log Interaction** to persist via `POST /interactions`.
2. **`edit_interaction`** *(mandatory)* — **updates the form the rep is reviewing** ("actually it
   was a call", "sentiment was negative", "add pediatric dosing to topics"). It returns a `patch`
   of **only the changed fields**, which the frontend merges into the current draft, so every
   other field stays exactly as it was.
3. **`search_interactions`** — looks up past interactions (by HCP and/or keyword) so the agent can
   ground an edit ("the visit last week") or answer "what did we last discuss with Dr. X."
4. **`schedule_followup`** — creates a follow-up task tied to an interaction whenever the rep
   mentions a next step, a promise to send something, or a requested return visit. Kept as its
   own tool (rather than a field on `log_interaction`) so the agent can create follow-ups
   mid-conversation or retroactively on older interactions.
5. **`hcp_insights`** — pulls an HCP's *entire* interaction history and asks the model for a
   relationship briefing: engagement trend, sentiment trajectory, and a recommended next best
   action — the kind of pre-visit briefing a rep would want before walking in.

### Note on the LLM: the mandated `gemma2-9b-it` has been decommissioned by Groq

The brief mandates `gemma2-9b-it` and separately says "you may also consider
`llama-3.3-70b-versatile` for context." **`gemma2-9b-it` is no longer available on Groq** — it has
been decommissioned and every call now returns:

```json
{"error":{"message":"The model `gemma2-9b-it` has been decommissioned and is no longer supported.
Please refer to https://console.groq.com/docs/deprecations ...","code":"model_decommissioned"}}
```

Because the mandated model can no longer be run at all, the agent loop uses
`llama-3.3-70b-versatile` — the exact model the brief names as the permitted alternative. A 70B model
is also the right engineering choice for this workload: reliable structured tool-calling across a
five-tool ReAct loop needs stronger instruction-following than Groq's small models provide (the
small models intermittently emit tool calls as plain text). The graph is fully model-agnostic —
change `PRIMARY_MODEL` in `backend/.env` to any current Groq model and it works unchanged (see
`app/agents/llm.py`), so the moment an equivalent small model is available it can be swapped in with
one line.

---

## 5. Project structure

```
avioai-crm-hcp/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── graph.py         # LangGraph StateGraph assembly
│   │   │   ├── llm.py           # Groq client factory (primary / context models)
│   │   │   ├── prompts.py       # System + task prompts
│   │   │   ├── state.py         # AgentState (messages, hcp_id, session_id)
│   │   │   └── tools/           # The 5 tools, one file each
│   │   ├── api/                 # FastAPI routers (hcps, interactions, chat)
│   │   ├── core/config.py       # Env-driven settings
│   │   ├── db/                  # SQLAlchemy models + Pydantic schemas
│   │   ├── main.py              # App entrypoint, CORS, router registration
│   │   └── seed.py              # Demo HCPs + interaction history
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/client.js        # Axios wrapper
│   │   ├── components/          # Sidebar, StructuredForm, ChatPanel, AgentTracePanel, …
│   │   ├── store/                # Redux Toolkit store + 3 slices
│   │   └── styles/index.css     # Design tokens + all component styles
│   ├── package.json
│   ├── Dockerfile
│   └── .env.example
├── docs/
│   ├── ARCHITECTURE.md          # Sequence diagram + design decisions
│   └── VIDEO_SCRIPT.md          # Talking points for the required submission video
├── docker-compose.yml
└── README.md                    # you are here
```

---

## 6. API reference (short version — full interactive docs at `/docs`)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/hcps` | List HCPs |
| POST | `/api/hcps` | Create an HCP |
| GET | `/api/interactions?hcp_id=` | List interactions, optionally filtered |
| POST | `/api/interactions` | Create via the structured form path |
| PATCH | `/api/interactions/{id}` | Manual edit (mirrors what `edit_interaction` does via chat) |
| POST | `/api/chat` | Send a message to the LangGraph agent; returns the reply **and** a `tool_trace` of exactly which tools ran, with what args and results — this is what powers the Agent Activity panel in the UI |

---

## 7. Design decisions worth knowing about

- **Both entry paths write the same schema and get the same LLM enrichment** — a rep isn't
  penalized for picking the form over the chat; `topics_discussed` gets summarized and
  sentiment-scored on the structured path too (`routes_interactions.py`), reusing the same
  prompts the chat tool uses.
- **Manual sentiment overrides the AI inference, never the other way round.** If a rep explicitly
  picks a sentiment in the form, that's respected; only an empty `topics_discussed` field
  triggers auto-inference.
- **Every agent edit is audited.** `edit_interaction` never silently overwrites — it diffs
  old/new values per field and appends a reasoned entry to `edit_history`, visible in the
  interaction history table.
- **LLM calls degrade gracefully, everywhere.** If Groq is unreachable or misconfigured, the
  structured form still saves the record (just without AI enrichment), and the chat endpoint
  returns a clear, actionable message instead of a 500. This was deliberately exercised during
  development in a network-restricted sandbox — see `docs/ARCHITECTURE.md` for how the agent
  loop itself was verified without live Groq access.
- **Session-scoped conversational memory.** LangGraph's `MemorySaver` checkpointer is keyed by a
  frontend-generated `session_id`, so "make it Tuesday, not Wednesday" resolves correctly within
  a chat — with the tradeoff that history resets on backend restart. For a real production
  deployment this would move to a persistent checkpointer (e.g. Postgres-backed).

---

## 8. What's out of scope

This is a Round-1, 36-hour take-home assignment, not a production CRM. Deliberately not built:
authentication/multi-rep accounts (the app assumes a single "Field Rep" persona), the voice-note
transcription affordance shown in the assignment's reference wireframe (needs a mic capture +
consent flow that's a separate feature in its own right), and Alembic migrations (the app calls
`create_all` on boot instead, which is fine at this scope but not how you'd manage schema changes
in production).
