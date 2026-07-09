import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { InteractionApi } from "../../api/client";

export const fetchInteractions = createAsyncThunk(
  "interactions/fetchForHCP",
  async (hcpId) => InteractionApi.list(hcpId)
);

export const createInteraction = createAsyncThunk(
  "interactions/create",
  async (payload) => InteractionApi.create(payload)
);

export const updateInteraction = createAsyncThunk(
  "interactions/update",
  async ({ id, patch }) => InteractionApi.update(id, patch)
);

const interactionsSlice = createSlice({
  name: "interactions",
  initialState: {
    items: [],
    status: "idle",
    submitStatus: "idle",
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchInteractions.pending, (state) => {
        state.status = "loading";
      })
      .addCase(fetchInteractions.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.items = action.payload;
      })
      .addCase(fetchInteractions.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.error.message;
      })
      .addCase(createInteraction.pending, (state) => {
        state.submitStatus = "loading";
      })
      .addCase(createInteraction.fulfilled, (state, action) => {
        state.submitStatus = "succeeded";
        state.items.unshift(action.payload);
      })
      .addCase(createInteraction.rejected, (state, action) => {
        state.submitStatus = "failed";
        state.error = action.error.message;
      })
      .addCase(updateInteraction.fulfilled, (state, action) => {
        const idx = state.items.findIndex((i) => i.id === action.payload.id);
        if (idx !== -1) state.items[idx] = action.payload;
      });
  },
});

export default interactionsSlice.reducer;
