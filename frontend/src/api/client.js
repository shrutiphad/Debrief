import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export const api = axios.create({ baseURL });

export const HCPApi = {
  list: () => api.get("/hcps").then((r) => r.data),
  create: (payload) => api.post("/hcps", payload).then((r) => r.data),
};

export const InteractionApi = {
  list: (hcpId) => api.get("/interactions", { params: hcpId ? { hcp_id: hcpId } : {} }).then((r) => r.data),
  create: (payload) => api.post("/interactions", payload).then((r) => r.data),
  update: (id, patch) => api.patch(`/interactions/${id}`, patch).then((r) => r.data),
  remove: (id) => api.delete(`/interactions/${id}`),
};

export const ChatApi = {
  send: (payload) => api.post("/chat", payload).then((r) => r.data),
};
