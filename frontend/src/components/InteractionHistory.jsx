import { useSelector } from "react-redux";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

// "2026-07-10" -> "10 Jul 2026" (parsed by hand to avoid timezone shifts).
function formatDate(iso) {
  if (!iso) return "—";
  const [y, m, d] = iso.split("-").map(Number);
  if (!y || !m || !d) return iso;
  return `${String(d).padStart(2, "0")} ${MONTHS[m - 1]} ${y}`;
}

export default function InteractionHistory() {
  const { items, status } = useSelector((s) => s.interactions);

  return (
    <div className="panel section-gap">
      <div className="panel-title">
        Interaction History
        {items.length > 0 && <span className="count-pill">{items.length}</span>}
      </div>
      {status === "loading" && <div className="empty-state">Loading…</div>}
      {status === "succeeded" && items.length === 0 && (
        <div className="empty-state">No interactions logged for this HCP yet.</div>
      )}
      {items.length > 0 && (
        <table className="history-table">
          <thead>
            <tr>
              <th>Date &amp; Time</th>
              <th>Type</th>
              <th>Summary</th>
              <th>Products</th>
              <th>Sentiment</th>
              <th>Follow-up</th>
            </tr>
          </thead>
          <tbody>
            {items.map((i) => (
              <tr key={i.id}>
                <td>
                  <div className="hist-date">{formatDate(i.interaction_date)}</div>
                  <div className="hist-time">{i.interaction_time ? `${i.interaction_time}` : "time not logged"}</div>
                </td>
                <td>
                  <span className="type-badge">{i.interaction_type}</span>
                  <span className={`channel-badge ${i.channel === "chat" ? "chat" : ""}`}>
                    {i.channel === "chat" ? "AI" : "manual"}
                  </span>
                </td>
                <td className="hist-summary">
                  {i.summary || i.topics_discussed || "—"}
                  {i.outcomes && <div className="edit-history-note">Outcome: {i.outcomes}</div>}
                  {i.edit_history?.length > 0 && (
                    <div className="edit-history-note">
                      Edited {i.edit_history.length}× via agent — last: “{i.edit_history[i.edit_history.length - 1].reason}”
                    </div>
                  )}
                </td>
                <td>
                  {i.products_discussed?.length ? (
                    <div className="hist-chips">
                      {i.products_discussed.map((p) => (
                        <span className="hist-chip" key={p}>
                          {p}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <span className="muted-dash">—</span>
                  )}
                </td>
                <td>
                  {i.sentiment ? <span className={`sentiment-badge ${i.sentiment}`}>{i.sentiment}</span> : <span className="muted-dash">—</span>}
                </td>
                <td>
                  {i.follow_up_required ? (
                    <span className="followup-badge" title={i.follow_up_notes || "Follow-up required"}>
                      ● Required
                    </span>
                  ) : (
                    <span className="muted-dash">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
