export default function Switch({ checked, onChange, disabled, label }) {
  return (
    <button
      type="button" role="switch" aria-checked={checked} aria-label={label} disabled={disabled}
      className={`switch ${checked ? "on" : ""}`} onClick={() => onChange(!checked)}
    ><span /></button>
  );
}
