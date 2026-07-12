import { createSlice } from "@reduxjs/toolkit";
import { sendChatMessage } from "./chatSlice";
import { createInteraction } from "./interactionsSlice";

// Browser-LOCAL date/time (not UTC) at the moment of the call — so a logged
// interaction is stamped with the rep's real local "now", not the server's UTC day.
function localDate() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
function localTime() {
  return new Date().toTimeString().slice(0, 5); // HH:MM
}

// Mirrors the fields the Interaction Details form renders. This is the "draft"
// the AI assistant fills in — the rep never edits it by hand.
export const emptyDraft = {
  interaction_type: "visit",
  interaction_date: localDate(),
  interaction_time: localTime(),
  attendees: [],
  products_discussed: [],
  samples_dropped: [],
  materials_shared: [],
  topics_discussed: "",
  outcomes: "",
  sentiment: null,
  follow_up_required: false,
  follow_up_notes: "",
};

// Only merge keys we actually render, and never overwrite with null/undefined.
function mergeDefined(base, incoming) {
  const out = { ...base };
  for (const key of Object.keys(emptyDraft)) {
    if (incoming[key] !== undefined && incoming[key] !== null) out[key] = incoming[key];
  }
  return out;
}

const draftSlice = createSlice({
  name: "draft",
  initialState: {
    fields: { ...emptyDraft },
    dirty: false, // true once the AI has put something in the form
    lastTouchedBy: null, // 'log' | 'edit' — drives the "AI just updated this" cue
  },
  reducers: {
    clearDraft(state) {
      state.fields = { ...emptyDraft };
      state.dirty = false;
      state.lastTouchedBy = null;
    },
    // Manual edit of a single field by the rep, before they log the interaction.
    // The AI fills the form, but the rep can still correct or complete anything here.
    setField(state, action) {
      const { key, value } = action.payload;
      state.fields[key] = value;
      state.dirty = true;
    },
  },
  extraReducers: (builder) => {
    // When a chat turn comes back, apply whatever the log/edit tools staged.
    builder.addCase(sendChatMessage.fulfilled, (state, action) => {
      const trace = action.payload.tool_trace || [];
      for (const t of trace) {
        if (t.tool === "log_interaction" && t.output?.draft) {
          // log = fill the whole form from scratch
          const filled = mergeDefined({ ...emptyDraft }, t.output.draft);
          // Stamp the creation date AND time at the moment of logging, in the rep's local
          // timezone, unless the rep explicitly stated one (the backend runs in UTC, so we
          // set these here to reflect the real local "today").
          if (!t.output.draft.interaction_date) filled.interaction_date = localDate();
          if (!t.output.draft.interaction_time) filled.interaction_time = localTime();
          state.fields = filled;
          state.dirty = true;
          state.lastTouchedBy = "log";
        } else if (t.tool === "edit_interaction" && t.output?.patch) {
          // edit = change only the fields the rep corrected, keep the rest
          state.fields = mergeDefined(state.fields, t.output.patch);
          state.dirty = true;
          state.lastTouchedBy = "edit";
        }
      }
    });
    // Once the rep saves, reset the form for the next interaction.
    builder.addCase(createInteraction.fulfilled, (state) => {
      state.fields = { ...emptyDraft };
      state.dirty = false;
      state.lastTouchedBy = null;
    });
  },
});

export const { clearDraft, setField } = draftSlice.actions;
export default draftSlice.reducer;
