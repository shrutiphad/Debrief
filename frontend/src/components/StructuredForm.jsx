import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { createInteraction } from "../store/slices/interactionsSlice";
import TagInput from "./TagInput";

const INTERACTION_TYPES = [
  { value: "visit", label: "In-person visit" },
  { value: "call", label: "Phone call" },
  { value: "email", label: "Email" },
  { value: "conference", label: "Conference / event" },
  { value: "sample_drop", label: "Sample drop" },
];

const emptyForm = {
  interaction_type: "visit",
  interaction_date: new Date().toISOString().slice(0, 10),
  interaction_time: new Date().toTimeString().slice(0, 5),
  attendees: [],
  products_discussed: [],
  samples_dropped: [],
  materials_shared: [],
  topics_discussed: "",
  outcomes: "",
  sentiment: null, // null = let the AI infer it from Topics Discussed
  follow_up_required: false,
  follow_up_notes: "",
};

const SENTIMENTS = ["positive", "neutral", "negative"];

export default function StructuredForm({ onLogged }) {
  const dispatch = useDispatch();
  const selectedHcpId = useSelector((s) => s.hcps.selectedId);
  const submitStatus = useSelector((s) => s.interactions.submitStatus);
  const [form, setForm] = useState(emptyForm);

  const set = (patch) => setForm((f) => ({ ...f, ...patch }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedHcpId) return;
    const result = await dispatch(createInteraction({ ...form, hcp_id: selectedHcpId, channel: "structured" }));
    if (result.meta.requestStatus === "fulfilled") {
      setForm(emptyForm);
      onLogged?.();
    }
  };

  return (
    <form className="panel" onSubmit={handleSubmit}>
      <div className="panel-title">Interaction Details</div>

      <div className="form-grid">
        <div className="field">
          <label>Interaction Type</label>
          <select value={form.interaction_type} onChange={(e) => set({ interaction_type: e.target.value })}>
            {INTERACTION_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label>Date</label>
          <input
            type="date"
            value={form.interaction_date}
            onChange={(e) => set({ interaction_date: e.target.value })}
          />
        </div>

        <div className="field">
          <label>Time</label>
          <input
            type="text"
            placeholder="HH:MM"
            value={form.interaction_time}
            onChange={(e) => set({ interaction_time: e.target.value })}
          />
        </div>

        <div className="field">
          <label>Attendees</label>
          <TagInput
            values={form.attendees}
            onChange={(v) => set({ attendees: v })}
            placeholder="Anyone else present…"
          />
        </div>

        <div className="field span-2">
          <label>
            Topics Discussed <span className="hint">— also used by the AI to generate the summary &amp; sentiment</span>
          </label>
          <textarea
            placeholder="Key discussion points…"
            value={form.topics_discussed}
            onChange={(e) => set({ topics_discussed: e.target.value })}
          />
        </div>

        <div className="field span-2">
          <label>Outcomes</label>
          <textarea
            placeholder="Key outcomes or agreements…"
            value={form.outcomes}
            onChange={(e) => set({ outcomes: e.target.value })}
          />
        </div>

        <div className="field span-2">
          <label>
            Observed / Inferred HCP Sentiment <span className="hint">— leave unset to let the AI infer it</span>
          </label>
          <div className="sentiment-row">
            {SENTIMENTS.map((s) => (
              <button
                type="button"
                key={s}
                className={`sentiment-option ${form.sentiment === s ? `selected ${s}` : ""}`}
                onClick={() => set({ sentiment: form.sentiment === s ? null : s })}
              >
                {s[0].toUpperCase() + s.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div className="field span-2">
          <label>Products Discussed</label>
          <TagInput
            values={form.products_discussed}
            onChange={(v) => set({ products_discussed: v })}
            placeholder="Type a product name and press Enter…"
          />
        </div>

        <div className="field">
          <label>Samples Distributed</label>
          <TagInput
            values={form.samples_dropped}
            onChange={(v) => set({ samples_dropped: v })}
            placeholder="e.g. Cardivax 10mg"
          />
        </div>

        <div className="field">
          <label>Materials Shared</label>
          <TagInput
            values={form.materials_shared}
            onChange={(v) => set({ materials_shared: v })}
            placeholder="e.g. Efficacy deck"
          />
        </div>

        <div className="field span-2">
          <div className="checkbox-row">
            <input
              type="checkbox"
              id="follow-up-required"
              checked={form.follow_up_required}
              onChange={(e) => set({ follow_up_required: e.target.checked })}
            />
            <label htmlFor="follow-up-required" style={{ fontWeight: 500 }}>
              Follow-up required
            </label>
          </div>
        </div>

        {form.follow_up_required && (
          <div className="field span-2">
            <label>Follow-up Notes</label>
            <textarea
              placeholder="What needs to happen next…"
              value={form.follow_up_notes}
              onChange={(e) => set({ follow_up_notes: e.target.value })}
            />
          </div>
        )}
      </div>

      <div className="form-actions">
        <button type="button" className="btn btn-ghost" onClick={() => setForm(emptyForm)}>
          Clear
        </button>
        <button type="submit" className="btn btn-primary" disabled={!selectedHcpId || submitStatus === "loading"}>
          {submitStatus === "loading" ? "Logging…" : "Log Interaction"}
        </button>
      </div>
    </form>
  );
}
