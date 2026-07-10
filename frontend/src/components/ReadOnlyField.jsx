// A single labelled, read-only form field. The Interaction Details form is driven
// entirely by the AI, so every field is display-only — this keeps that markup in
// one place instead of repeating label/hint wrappers for each field.
export default function ReadOnlyField({ label, hint, span, children }) {
  return (
    <div className={`field ${span ? "span-2" : ""}`}>
      <label>
        {label}
        {hint && <span className="hint"> — {hint}</span>}
      </label>
      {children}
    </div>
  );
}
