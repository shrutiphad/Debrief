import { useDispatch, useSelector } from "react-redux";
import { createInteraction } from "../store/slices/interactionsSlice";
import { clearDraft } from "../store/slices/draftSlice";
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
// the AI assistant on the right fills and edits it via the log/edit tools. The fields
// are therefore rendered read-only; the rep only reviews and saves.
export default function StructuredForm() {
  const dispatch = useDispatch();
  const selectedHcpId = useSelector((s) => s.hcps.selectedId);
  const submitStatus = useSelector((s) => s.interactions.submitStatus);
  const { fields, dirty, lastTouchedBy } = useSelector((s) => s.draft);

  const handleSave = async () => {
    if (!selectedHcpId || !dirty) return;
    const result = await dispatch(
      createInteraction({ ...fields, hcp_id: selectedHcpId, channel: "chat" })
    );
    // draftSlice clears the form on createInteraction.fulfilled
    return result;
  };

  return (
    <div className="panel form-panel">
      <div className="panel-title">
        Interaction Details
        <span className={`ai-driven-pill ${lastTouchedBy ? "active" : ""}`}>
          {lastTouchedBy ? "✦ Updated by AI" : "✦ AI-filled"}
        </span>
      </div>
      <p className="form-hint-lead">
        Don't type here — describe the visit to the assistant on the right and it fills this form.
      </p>

      <div className="form-grid">
        <div className="field">
          <label>Interaction Type</label>
          <input type="text" value={INTERACTION_TYPE_LABELS[fields.interaction_type] || fields.interaction_type} readOnly />
        </div>

        <div className="field">
          <label>Date</label>
          <input type="text" value={fields.interaction_date || ""} readOnly />
        </div>

        <div className="field">
          <label>Time</label>
          <input type="text" value={fields.interaction_time || "—"} readOnly />
        </div>

        <div className="field">
          <label>Attendees</label>
          <TagInput values={fields.attendees || []} readOnly />
        </div>

        <div className="field span-2">
          <label>
            Topics Discussed <span className="hint">— summarized by the AI</span>
          </label>
          <textarea value={fields.topics_discussed || ""} readOnly placeholder="—" />
        </div>

        <div className="field span-2">
          <label>Outcomes</label>
          <textarea value={fields.outcomes || ""} readOnly placeholder="—" />
        </div>

        <div className="field span-2">
          <label>
            HCP Sentiment <span className="hint">— inferred by the AI</span>
          </label>
          <div className="sentiment-row">
            {SENTIMENTS.map((s) => (
              <div key={s} className={`sentiment-option ${fields.sentiment === s ? `selected ${s}` : ""}`}>
                {s[0].toUpperCase() + s.slice(1)}
              </div>
            ))}
          </div>
        </div>

        <div className="field span-2">
          <label>Products Discussed</label>
          <TagInput values={fields.products_discussed || []} readOnly />
        </div>

        <div className="field">
          <label>Samples Distributed</label>
          <TagInput values={fields.samples_dropped || []} readOnly />
        </div>

        <div className="field">
          <label>Materials Shared</label>
          <TagInput values={fields.materials_shared || []} readOnly />
        </div>

        <div className="field span-2">
          <div className="checkbox-row">
            <input type="checkbox" id="follow-up-required" checked={!!fields.follow_up_required} readOnly disabled />
            <label htmlFor="follow-up-required" style={{ fontWeight: 500 }}>
              Follow-up required
            </label>
          </div>
        </div>

        {fields.follow_up_required && (
          <div className="field span-2">
            <label>Follow-up Notes</label>
            <textarea value={fields.follow_up_notes || ""} readOnly placeholder="—" />
          </div>
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
