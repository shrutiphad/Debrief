import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { fetchInteractions } from "../store/slices/interactionsSlice";
import { resetSession } from "../store/slices/chatSlice";
import { clearDraft } from "../store/slices/draftSlice";
import StructuredForm from "./StructuredForm";
import ChatPanel from "./ChatPanel";
import AgentTracePanel from "./AgentTracePanel";
import InteractionHistory from "./InteractionHistory";

export default function LogInteractionScreen() {
  const dispatch = useDispatch();
  const selectedHcp = useSelector((s) => s.hcps.items.find((h) => h.id === s.hcps.selectedId));

  useEffect(() => {
    if (selectedHcp) {
      dispatch(fetchInteractions(selectedHcp.id));
      dispatch(resetSession());
      dispatch(clearDraft());
    }
  }, [selectedHcp?.id, dispatch]);

  if (!selectedHcp) {
    return <div className="empty-state">Select an HCP from the directory to log an interaction.</div>;
  }

  return (
    <div>
      <div className="content-header">
        <div className="content-title">Log HCP Interaction — {selectedHcp.name}</div>
        <div className="content-sub">
          {selectedHcp.specialty} · {selectedHcp.institution} · {selectedHcp.city}
        </div>
      </div>

      {/* Split screen: AI-driven form on the left, assistant chat on the right. */}
      <div className="split-screen">
        <StructuredForm />
        <div className="chat-column">
          <ChatPanel />
          <AgentTracePanel />
        </div>
      </div>

      <div className="section-gap">
        <InteractionHistory />
      </div>
    </div>
  );
}
