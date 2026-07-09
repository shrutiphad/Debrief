import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { fetchInteractions } from "../store/slices/interactionsSlice";
import { resetSession } from "../store/slices/chatSlice";
import StructuredForm from "./StructuredForm";
import ChatPanel from "./ChatPanel";
import InteractionHistory from "./InteractionHistory";

export default function LogInteractionScreen() {
  const dispatch = useDispatch();
  const selectedHcp = useSelector((s) => s.hcps.items.find((h) => h.id === s.hcps.selectedId));
  const [mode, setMode] = useState("chat");

  useEffect(() => {
    if (selectedHcp) {
      dispatch(fetchInteractions(selectedHcp.id));
      dispatch(resetSession());
    }
  }, [selectedHcp?.id, dispatch]);

  if (!selectedHcp) {
    return <div className="empty-state">Select an HCP from the directory to log an interaction.</div>;
  }

  return (
    <div>
      <div className="content-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <div className="content-title">Log HCP Interaction — {selectedHcp.name}</div>
          <div className="content-sub">
            {selectedHcp.specialty} · {selectedHcp.institution} · {selectedHcp.city}
          </div>
        </div>
        <div className="mode-toggle">
          <button className={mode === "chat" ? "active" : ""} onClick={() => setMode("chat")}>
            Conversational
          </button>
          <button className={mode === "structured" ? "active" : ""} onClick={() => setMode("structured")}>
            Structured Form
          </button>
        </div>
      </div>

      {mode === "chat" ? <ChatPanel /> : <StructuredForm />}

      <InteractionHistory />
    </div>
  );
}
