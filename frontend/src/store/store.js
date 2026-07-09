import { configureStore } from "@reduxjs/toolkit";
import hcpReducer from "./slices/hcpSlice";
import interactionsReducer from "./slices/interactionsSlice";
import chatReducer from "./slices/chatSlice";

export const store = configureStore({
  reducer: {
    hcps: hcpReducer,
    interactions: interactionsReducer,
    chat: chatReducer,
  },
});
