import { useDispatch, useSelector } from "react-redux";
import { createInteraction } from "../store/slices/interactionsSlice";
import { clearDraft } from "../store/slices/draftSlice";
import ReadOnlyField from "./ReadOnlyField";
import TagInput from "./TagInput";

const INTERACTION_TYPE_LABELS = {
  visit: "In-person visit",
  call: "Phone call",
  email: "Email",
  conference: "Conference / event",
  sample_drop: "Sample drop",
};

const SENTIMENTS = ["positive", "neutral", "negative"];

// The Interaction Details form. Per the task, the rep does NOT fill this by hand —
// the AI assistant fills and edits it via the log/edit tools, so every field is
// display-only. The rep only reviews and saves.
export default function StructuredForm() {
  const dispatch = useDispatch();
  const selectedHcpId = useSelector((s) => s.hcps.selectedId);
  const submitStatus = useSelector((s) => s.interactions.submitStatus);
  const { fields, dirty, lastTouchedBy } = useSelector((s) => s.draft);

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
        You don't type here — describe the visit to the assistant on the right and it fills this form.
      </p>

      <div className="form-grid">
        <ReadOnlyField label="Interaction Type">
          <input type="text" value={INTERACTION_TYPE_LABELS[fields.interaction_type] || fields.interaction_type} readOnly />
        </ReadOnlyField>

        <ReadOnlyField label="Date">
          <input type="text" value={fields.interaction_date || "—"} readOnly />
        </ReadOnlyField>

        <ReadOnlyField label="Time">
          <input type="text" value={fields.interaction_time || "—"} readOnly />
        </ReadOnlyField>

        <ReadOnlyField label="Attendees">
          <TagInput values={fields.attendees || []} readOnly />
        </ReadOnlyField>

        <ReadOnlyField label="Topics Discussed" hint="summarized by the AI" span>
          <textarea value={fields.topics_discussed || ""} readOnly placeholder="—" />
        </ReadOnlyField>

        <ReadOnlyField label="Outcomes" span>
          <textarea value={fields.outcomes || ""} readOnly placeholder="—" />
        </ReadOnlyField>

        <ReadOnlyField label="HCP Sentiment" hint="inferred by the AI" span>
          <div className="sentiment-row">
            {SENTIMENTS.map((s) => (
              <div key={s} className={`sentiment-option ${fields.sentiment === s ? `selected ${s}` : ""}`}>
                {s[0].toUpperCase() + s.slice(1)}
              </div>
            ))}
          </div>
        </ReadOnlyField>

        <ReadOnlyField label="Products Discussed" span>
          <TagInput values={fields.products_discussed || []} readOnly />
        </ReadOnlyField>

        <ReadOnlyField label="Samples Distributed">
          <TagInput values={fields.samples_dropped || []} readOnly />
        </ReadOnlyField>

        <ReadOnlyField label="Materials Shared">
          <TagInput values={fields.materials_shared || []} readOnly />
        </ReadOnlyField>

        <div className="field span-2">
          <div className="checkbox-row">
            <input type="checkbox" id="follow-up-required" checked={!!fields.follow_up_required} readOnly disabled />
            <label htmlFor="follow-up-required" style={{ fontWeight: 500 }}>
              Follow-up required
            </label>
          </div>
        </div>

        {fields.follow_up_required && (
          <ReadOnlyField label="Follow-up Notes" span>
            <textarea value={fields.follow_up_notes || ""} readOnly placeholder="—" />
          </ReadOnlyField>
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
