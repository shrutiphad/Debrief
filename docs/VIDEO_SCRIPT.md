# Video Walkthrough — Talking Points

The assignment requires a video explaining the submission. This is a suggested script/outline —
adapt it to how you actually talk, don't read it verbatim. Aim for 8-12 minutes.

---

## 1. Open — what you built (60-90 sec)

- "This is the Log Interaction screen for AVIOAI's CRM — it lets a pharma field rep log an HCP
  interaction two ways: a structured form, or talking to an AI agent in plain language."
- Show the app once, HCP selected, both mode toggles visible. Don't demo yet — just orient.
- One sentence on stack: "React and Redux on the frontend, FastAPI and LangGraph on the backend,
  Groq's gemma2-9b-it as the primary model with llama-3.3-70b-versatile for the longer-context
  insights tool, Postgres for storage."

## 2. Structured form demo (60-90 sec)

- Pick an HCP from the sidebar.
- Fill the form: type, date/time, attendees, products, samples, topics discussed, outcomes.
- Point out: "Even though I typed this by hand, submitting still calls the LLM once — it
  summarizes what I wrote in Topics Discussed and infers sentiment, unless I set sentiment
  manually myself." Toggle a sentiment button to show the manual override.
- Submit → show it land in Interaction History below with the AI-written summary.

## 3. Conversational chat demo — the core of the assignment (3-4 min)

This is the section graders will weight most heavily — take your time here.

- Switch to Conversational mode. Point at the Agent Activity panel: "This is a live view into
  the LangGraph pipeline — you'll see it light up as the agent reasons and calls tools."
- Type something naturally: *"Just met Dr. Mehta, discussed Cardivax, she was really positive and
  wants samples dropped off next visit."*
- While it's "thinking," narrate the pipeline stages lighting up: message received → agent
  reasoning → tool execution → database write → response synthesized.
- When the reply lands, show the **Agent Activity** panel's tool call card: tool name
  (`log_interaction`), and the args it extracted on its own — products, sentiment intent,
  follow-up. Say explicitly: *"I never told it 'sentiment: positive' or 'follow_up_required:
  true' — it extracted both from my sentence."*
- Scroll down, show the new row appear in Interaction History with the AI summary.
- **Demo an edit**: *"Actually, she also asked about pediatric dosing."* Show the agent calls
  `edit_interaction`, and point out the edit history note now visible on that row ("Edited 1× via
  agent").
- **Demo a follow-up**: *"Send her the Phase III safety study by Friday."* Show
  `schedule_followup` fire in the trace panel.
- **Demo search / insights**: ask *"How are we doing with Dr. Mehta overall?"* — show
  `hcp_insights` fire, and read out the briefing it returns. Mention: *"This one specifically
  runs on llama-3.3-70b-versatile instead of gemma2-9b-it, because it's reasoning over the whole
  interaction history rather than one message — that's the 'for context' model swap the brief
  mentioned."*

## 4. Code walkthrough (3-4 min)

Open the repo in your editor and hit these files, roughly in this order:

1. **`backend/app/agents/graph.py`** — the `StateGraph`: agent node, tools node, conditional
   edge. Explain the loop in one sentence: "if the LLM's response has tool calls, run them and
   loop back; otherwise we're done."
2. **`backend/app/agents/tools/log_interaction.py`** — show the Pydantic `args_schema` (this is
   what tells the LLM what arguments to extract), and the two extra LLM calls inside the tool
   body for summary/sentiment.
3. **`backend/app/agents/tools/hcp_insights.py`** — point at `get_context_llm()` — this is the
   one tool using the 70B model.
4. **`backend/app/api/routes_chat.py`** — `_extract_trace()`: how the tool-call trace shown in
   the UI is derived directly from the graph's message list, not faked client-side.
5. **`frontend/src/components/AgentTracePanel.jsx`** — briefly, just to connect the dots: this
   renders `tool_trace` from that same API response.
6. **`frontend/src/store/slices/chatSlice.js`** — the Redux slice managing the conversation; note
   `sessionId` is what ties a chat to LangGraph's `MemorySaver` checkpointer via `thread_id`.

## 5. Close (30-45 sec)

- One sentence on what's deliberately out of scope and why (see README §8 — auth, voice notes,
  migrations) — shows you know the difference between "assignment scope" and "production scope."
- Mention the README/ARCHITECTURE.md have more detail than you had time to cover live.
- Thank them, stop recording.

---

## Recording tips

- Record the browser and editor in the same take if you can — cutting between separate recordings
  takes longer to edit than it saves.
- If `GROQ_API_KEY` behaves inconsistently for `gemma2-9b-it` tool-calling right before you record,
  set `AGENT_MODEL=context` in `backend/.env` to fall back to `llama-3.3-70b-versatile` for the
  whole agent loop — see README §4 — rather than debugging live on camera.
- Seed data (`python -m app.seed`) gives you Dr. Mehta with two prior visits already logged, so the
  `hcp_insights` demo has real history to reason over from the very first run.
