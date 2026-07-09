import { useEffect, useRef, useState } from "react";
import { useSelector } from "react-redux";

const PIPELINE = [
  { key: "receive", label: "Rep message received" },
  { key: "agent", label: "Agent reasoning · gemma2-9b-it" },
  { key: "tools", label: "Tool execution · LangGraph ToolNode" },
  { key: "db", label: "CRM database write" },
  { key: "reply", label: "Agent response synthesized" },
];

export default function AgentTracePanel() {
  const status = useSelector((s) => s.chat.status);
  const toolTrace = useSelector((s) => s.chat.toolTrace);
  const [liveIndex, setLiveIndex] = useState(-1);
  const timerRef = useRef(null);

  useEffect(() => {
    if (status === "thinking") {
      setLiveIndex(0);
      let i = 0;
      timerRef.current = setInterval(() => {
        i = Math.min(i + 1, PIPELINE.length - 2); // hold before final "reply" node until response lands
        setLiveIndex(i);
      }, 550);
    } else {
      clearInterval(timerRef.current);
      if (status === "idle") {
        setLiveIndex(PIPELINE.length - 1);
        const t = setTimeout(() => setLiveIndex(-1), 1200);
        return () => clearTimeout(t);
      }
      setLiveIndex(-1);
    }
    return () => clearInterval(timerRef.current);
  }, [status]);

  return (
    <div className="trace-panel">
      <div className="panel-title">⚙ Agent Activity</div>

      <div className="trace-pipeline">
        {PIPELINE.map((node, idx) => (
          <div key={node.key} className={`trace-node ${idx === liveIndex ? "live" : ""}`}>
            <span className="line" />
            <span className="dot" />
            <span className="trace-node-label">{node.label}</span>
          </div>
        ))}
      </div>

      <div className="trace-calls">
        {toolTrace.length === 0 && status !== "thinking" && (
          <div className="trace-empty">Tool calls the agent makes this turn will appear here in real time.</div>
        )}
        {toolTrace.map((call, idx) => (
          <div className="trace-call" key={idx}>
            <div className="trace-call-name">
              <span className={`status-dot ${call.status === "error" ? "error" : ""}`} />
              {call.tool}
            </div>
            <div className="trace-call-detail">
              {Object.entries(call.input || {})
                .filter(([k]) => k !== "raw_notes")
                .slice(0, 3)
                .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") || "—" : String(v)}`)
                .join(" · ")}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
