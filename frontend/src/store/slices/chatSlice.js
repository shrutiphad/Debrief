import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { ChatApi } from "../../api/client";

function newSessionId() {
  return `sess_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

export const sendChatMessage = createAsyncThunk(
  "chat/send",
  async ({ sessionId, hcpId, message }) => {
    return ChatApi.send({ session_id: sessionId, hcp_id: hcpId, message });
  }
);

const chatSlice = createSlice({
  name: "chat",
  initialState: {
    sessionId: newSessionId(),
    messages: [], // { role: 'human' | 'agent' | 'system-note', content }
    toolTrace: [], // last turn's tool calls, for the Agent Activity panel
    status: "idle", // idle | thinking | error
    lastInteractionTouched: null, // interaction_id most recently created/edited, so UI can refresh history
  },
  reducers: {
    resetSession(state) {
      state.sessionId = newSessionId();
      state.messages = [];
      state.toolTrace = [];
      state.status = "idle";
    },
    pushHumanMessage(state, action) {
      state.messages.push({ role: "human", content: action.payload });
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendChatMessage.pending, (state) => {
        state.status = "thinking";
        state.toolTrace = [];
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.status = "idle";
        state.messages.push({ role: "agent", content: action.payload.reply });
        state.toolTrace = action.payload.tool_trace || [];
        const touched = state.toolTrace.find((t) =>
          ["log_interaction", "edit_interaction", "schedule_followup"].includes(t.tool)
        );
        if (touched) {
          state.lastInteractionTouched =
            touched.output?.interaction_id || touched.output?.follow_up_id || Date.now();
        }
      })
      .addCase(sendChatMessage.rejected, (state, action) => {
        state.status = "error";
        state.messages.push({
          role: "system-note",
          content: `Something went wrong reaching the agent: ${action.error.message}`,
        });
      });
  },
});

export const { resetSession, pushHumanMessage } = chatSlice.actions;
export default chatSlice.reducer;
