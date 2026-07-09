import { useSelector } from "react-redux";

export default function InteractionHistory() {
  const { items, status } = useSelector((s) => s.interactions);

  return (
    <div className="panel section-gap">
      <div className="panel-title">Interaction History</div>
      {status === "loading" && <div className="empty-state">Loading…</div>}
      {status === "succeeded" && items.length === 0 && (
        <div className="empty-state">No interactions logged for this HCP yet.</div>
      )}
      {items.length > 0 && (
        <table className="history-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Type</th>
              <th>Summary</th>
              <th>Attendees</th>
              <th>Products</th>
              <th>Sentiment</th>
              <th>Follow-up</th>
            </tr>
          </thead>
          <tbody>
            {items.map((i) => (
              <tr key={i.id}>
                <td>
                  {i.interaction_date}
                  {i.interaction_time && <div className="hint">{i.interaction_time}</div>}
                </td>
                <td>
                  {i.interaction_type} <span className="channel-badge">{i.channel}</span>
                </td>
                <td style={{ maxWidth: 300 }}>
                  {i.summary || i.topics_discussed || "—"}
                  {i.outcomes && <div className="edit-history-note">Outcome: {i.outcomes}</div>}
                  {i.edit_history?.length > 0 && (
                    <div className="edit-history-note">
                      Edited {i.edit_history.length}× via agent — last: “{i.edit_history[i.edit_history.length - 1].reason}”
                    </div>
                  )}
                </td>
                <td>{i.attendees?.join(", ") || "—"}</td>
                <td>{i.products_discussed?.join(", ") || "—"}</td>
                <td>
                  {i.sentiment ? <span className={`sentiment-badge ${i.sentiment}`}>{i.sentiment}</span> : "—"}
                </td>
                <td>{i.follow_up_required ? i.follow_up_notes || "Yes" : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
