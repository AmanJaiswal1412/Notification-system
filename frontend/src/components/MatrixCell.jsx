import Switch from "./Switch.jsx";
import StatusBadge from "./StatusBadge.jsx";

// One cell of the admin table: shows the template (if any) + on/off + actions.
export default function MatrixCell({ cell, channel, busy, onCreate, onEdit, onToggle, onTest }) {
  if (!cell) {
    return <button className="btn ghost" onClick={onCreate}>+ Create template</button>;
  }
  const summary = cell.subject || cell.title || cell.body;
  return (
    <div className="cell">
      <div className="cell-head">
        <span className="cell-title" title={cell.body}>{summary}</span>
        <Switch checked={cell.is_enabled} disabled={busy} onChange={onToggle} label="Enabled" />
      </div>
      {channel === "whatsapp" && <StatusBadge value={cell.wa_status} />}
      <div className="row gap">
        <button className="btn small" onClick={onEdit}>Edit</button>
        <button className="btn small" disabled={busy} onClick={onTest}>Test send</button>
      </div>
    </div>
  );
}
