import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { HCPApi } from "../../api/client";

export const fetchHCPs = createAsyncThunk("hcps/fetchAll", async () => HCPApi.list());

const hcpSlice = createSlice({
  name: "hcps",
  initialState: {
    items: [],
    selectedId: null,
    status: "idle", // idle | loading | succeeded | failed
    error: null,
  },
  reducers: {
    selectHCP(state, action) {
      state.selectedId = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchHCPs.pending, (state) => {
        state.status = "loading";
      })
      .addCase(fetchHCPs.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.items = action.payload;
        if (!state.selectedId && action.payload.length > 0) {
          state.selectedId = action.payload[0].id;
        }
      })
      .addCase(fetchHCPs.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.error.message;
      });
  },
});

export const { selectHCP } = hcpSlice.actions;
export default hcpSlice.reducer;
