export default function Field({ label, id, ...props }) {
  return (
    <div className="form-group">
      <label htmlFor={id}>{label}</label>
      <input id={id} className="campo-input" {...props} />
    </div>
  );
}
