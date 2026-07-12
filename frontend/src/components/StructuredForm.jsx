import { useDispatch, useSelector } from "react-redux";
import { createInteraction } from "../store/slices/interactionsSlice";
import { clearDraft, setField } from "../store/slices/draftSlice";
import FormField from "./FormField";
import TagInput from "./TagInput";

const INTERACTION_TYPES = [
  { value: "visit", label: "In-person visit" },
  { value: "call", label: "Phone call" },
  { value: "email", label: "Email" },
  { value: "conference", label: "Conference / event" },
  { value: "sample_drop", label: "Sample drop" },
];

const SENTIMENTS = ["positive", "neutral", "negative"];

// The Interaction Details form. The AI assistant fills it from the chat, but every field
// stays editable — the rep can correct or complete anything before clicking Log Interaction.
export default function StructuredForm() {
  const dispatch = useDispatch();
  const selectedHcpId = useSelector((s) => s.hcps.selectedId);
  const submitStatus = useSelector((s) => s.interactions.submitStatus);
  const { fields, dirty, lastTouchedBy } = useSelector((s) => s.draft);

  const set = (key, value) => dispatch(setField({ key, value }));

  const handleSave = () => {
    if (!selectedHcpId || !dirty) return;
    dispatch(createInteraction({ ...fields, hcp_id: selectedHcpId, channel: "chat" }));
    // draftSlice clears the form on createInteraction.fulfilled
  };

  return (
    <div className="panel form-panel">
      <div className="panel-title">
        Interaction Details
        <span className={`ai-driven-pill ${lastTouchedBy ? "active" : ""}`}>
          {lastTouchedBy === "edit" ? "✦ Updated by AI" : "✦ AI-filled"}
        </span>
      </div>
      <p className="form-hint-lead">
        The assistant fills this from your chat — you can also edit any field here before you log it.
      </p>

      <div className="form-grid">
        <FormField label="Interaction Type">
          <select value={fields.interaction_type || "visit"} onChange={(e) => set("interaction_type", e.target.value)}>
            {INTERACTION_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </FormField>

        <FormField label="Date">
          <input type="date" value={fields.interaction_date || ""} onChange={(e) => set("interaction_date", e.target.value)} />
        </FormField>

        <FormField label="Time">
          <input type="time" value={fields.interaction_time || ""} onChange={(e) => set("interaction_time", e.target.value)} />
        </FormField>

        <FormField label="Attendees">
          <TagInput
            values={fields.attendees || []}
            onChange={(v) => set("attendees", v)}
            placeholder="Anyone else present…"
          />
        </FormField>

        <FormField label="Topics Discussed" hint="summarized by the AI" span>
          <textarea
            value={fields.topics_discussed || ""}
            onChange={(e) => set("topics_discussed", e.target.value)}
            placeholder="Key discussion points…"
          />
        </FormField>

        <FormField label="Outcomes" span>
          <textarea
            value={fields.outcomes || ""}
            onChange={(e) => set("outcomes", e.target.value)}
            placeholder="Key outcomes or agreements…"
          />
        </FormField>

        <FormField label="HCP Sentiment" hint="inferred by the AI, tap to change" span>
          <div className="sentiment-row">
            {SENTIMENTS.map((s) => (
              <button
                type="button"
                key={s}
                className={`sentiment-option ${fields.sentiment === s ? `selected ${s}` : ""}`}
                onClick={() => set("sentiment", fields.sentiment === s ? null : s)}
              >
                {s[0].toUpperCase() + s.slice(1)}
              </button>
            ))}
          </div>
        </FormField>

        <FormField label="Products Discussed" span>
          <TagInput
            values={fields.products_discussed || []}
            onChange={(v) => set("products_discussed", v)}
            placeholder="Type a product name and press Enter…"
          />
        </FormField>

        <FormField label="Samples Distributed">
          <TagInput
            values={fields.samples_dropped || []}
            onChange={(v) => set("samples_dropped", v)}
            placeholder="e.g. Cardivax 10mg"
          />
        </FormField>

        <FormField label="Materials Shared">
          <TagInput
            values={fields.materials_shared || []}
            onChange={(v) => set("materials_shared", v)}
            placeholder="e.g. Efficacy deck"
          />
        </FormField>

        <div className="field span-2">
          <div className="checkbox-row">
            <input
              type="checkbox"
              id="follow-up-required"
              checked={!!fields.follow_up_required}
              onChange={(e) => set("follow_up_required", e.target.checked)}
            />
            <label htmlFor="follow-up-required" style={{ fontWeight: 500 }}>
              Follow-up required
            </label>
          </div>
        </div>

        {fields.follow_up_required && (
          <FormField label="Follow-up Notes" span>
            <textarea
              value={fields.follow_up_notes || ""}
              onChange={(e) => set("follow_up_notes", e.target.value)}
              placeholder="What needs to happen next…"
            />
          </FormField>
        )}
      </div>

      <div className="form-actions">
        <button type="button" className="btn btn-ghost" onClick={() => dispatch(clearDraft())} disabled={!dirty}>
          Clear
        </button>
        <button
          type="button"
          className="btn btn-primary"
          onClick={handleSave}
          disabled={!selectedHcpId || !dirty || submitStatus === "loading"}
        >
          {submitStatus === "loading" ? "Saving…" : "Log Interaction"}
        </button>
      </div>
    </div>
  );
}
