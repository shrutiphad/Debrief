import { createSlice } from "@reduxjs/toolkit";
import { sendChatMessage } from "./chatSlice";
import { createInteraction } from "./interactionsSlice";

// Mirrors the fields the Interaction Details form renders. This is the "draft"
// the AI assistant fills in — the rep never edits it by hand.
export const emptyDraft = {
  interaction_type: "visit",
  interaction_date: new Date().toISOString().slice(0, 10),
  interaction_time: "",
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
  },
  extraReducers: (builder) => {
    // When a chat turn comes back, apply whatever the log/edit tools staged.
    builder.addCase(sendChatMessage.fulfilled, (state, action) => {
      const trace = action.payload.tool_trace || [];
      for (const t of trace) {
        if (t.tool === "log_interaction" && t.output?.draft) {
          // log = fill the whole form from scratch
          state.fields = mergeDefined({ ...emptyDraft }, t.output.draft);
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

export const { clearDraft } = draftSlice.actions;
export default draftSlice.reducer;
