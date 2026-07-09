import { useEffect, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { pushHumanMessage, sendChatMessage } from "../store/slices/chatSlice";
import { fetchInteractions } from "../store/slices/interactionsSlice";
import AgentTracePanel from "./AgentTracePanel";

export default function ChatPanel() {
  const dispatch = useDispatch();
  const { sessionId, messages, status, lastInteractionTouched } = useSelector((s) => s.chat);
  const selectedHcp = useSelector((s) => s.hcps.items.find((h) => h.id === s.hcps.selectedId));
  const [draft, setDraft] = useState("");
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, status]);

  useEffect(() => {
    if (lastInteractionTouched && selectedHcp) {
      dispatch(fetchInteractions(selectedHcp.id));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lastInteractionTouched]);

  const handleSend = () => {
    const text = draft.trim();
    if (!text || status === "thinking") return;
    dispatch(pushHumanMessage(text));
    setDraft("");
    dispatch(sendChatMessage({ sessionId, hcpId: selectedHcp?.id, message: text }));
  };

  return (
    <div className="chat-layout">
      <div className="chat-panel">
        <div className="chat-messages" ref={scrollRef}>
          {messages.length === 0 && (
            <div className="chat-empty">
              Tell the agent what happened — e.g. “Just met {selectedHcp?.name || "the HCP"}, discussed Cardivax,
              she was positive and wants samples next visit.” It will log the interaction, extract the details, and
              confirm back to you.
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`chat-bubble ${m.role}`}>
              {m.content}
            </div>
          ))}
          {status === "thinking" && (
            <div className="chat-bubble agent">
              <span className="typing-dots">
                <span />
                <span />
                <span />
              </span>
            </div>
          )}
        </div>
        <div className="chat-input-row">
          <textarea
            placeholder={selectedHcp ? `Message about ${selectedHcp.name}…` : "Select an HCP to begin…"}
            value={draft}
            disabled={!selectedHcp}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
          />
          <button className="btn btn-primary" onClick={handleSend} disabled={!selectedHcp || status === "thinking"}>
            Send
          </button>
        </div>
      </div>
      <AgentTracePanel />
    </div>
  );
}
