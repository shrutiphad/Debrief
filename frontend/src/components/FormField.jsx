// A single labelled field wrapper. Keeps the label/hint markup in one place so the
// form fields (all bound to the AI-filled draft, but still manually editable) stay tidy.
export default function FormField({ label, hint, span, children }) {
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
