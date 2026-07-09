import { useMemo, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { selectHCP } from "../store/slices/hcpSlice";

export default function Sidebar() {
  const dispatch = useDispatch();
  const { items, selectedId } = useSelector((s) => s.hcps);
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return items;
    return items.filter(
      (h) =>
        h.name.toLowerCase().includes(q) ||
        (h.specialty || "").toLowerCase().includes(q) ||
        (h.institution || "").toLowerCase().includes(q)
    );
  }, [items, query]);

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-title">HCP Directory</div>
        <input
          className="search-input"
          placeholder="Search by name, specialty…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>
      <div className="hcp-list">
        {filtered.length === 0 && <div className="empty-state">No HCPs match “{query}”.</div>}
        {filtered.map((hcp) => (
          <button
            key={hcp.id}
            className={`hcp-card ${hcp.id === selectedId ? "active" : ""}`}
            onClick={() => dispatch(selectHCP(hcp.id))}
          >
            <div className="hcp-card-name">
              {hcp.name} <span className={`tier-badge tier-${hcp.tier}`}>{hcp.tier}</span>
            </div>
            <div className="hcp-card-meta">
              {hcp.specialty || "—"} · {hcp.institution || "—"}
            </div>
          </button>
        ))}
      </div>
    </aside>
  );
}
