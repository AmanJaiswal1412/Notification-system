import { useCallback, useEffect, useState } from "react";
import { adminApi } from "../api/admin.js";
import MatrixCell from "../components/MatrixCell.jsx";
import NewTriggerModal from "../components/NewTriggerModal.jsx";
import TemplateModal from "../components/TemplateModal.jsx";
import TestSendModal from "../components/TestSendModal.jsx";
import Toast from "../components/Toast.jsx";
import Switch from "../components/Switch.jsx";
import { useToast } from "../lib/useToast.js";

const CHANNELS = [
  { key: "whatsapp", label: "WhatsApp" },
  { key: "email", label: "Email" },
  { key: "push", label: "Web Push" },
];

export default function AdminPage() {
  const [rows, setRows] = useState([]);
  const [variables, setVariables] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(null);
  const [editing, setEditing] = useState(null);   // {trigger, channel}
  const [testing, setTesting] = useState(null);   // {template, channel}
  const [newTrigger, setNewTrigger] = useState(false);
  const [toast, notify] = useToast();

  const load = useCallback(async () => {
    try {
      const [t, v] = await Promise.all([adminApi.triggers(), adminApi.variables()]);
      setRows(t); setVariables(v);
    } catch (e) { notify(e.message, "err"); } finally { setLoading(false); }
  }, [notify]);
  useEffect(() => { load(); }, [load]);

  const toggle = async (cell) => {
    setBusy(cell.id);
    try { await adminApi.toggleTemplate(cell.id, !cell.is_enabled); await load(); }
    catch (e) { notify(e.message, "err"); } finally { setBusy(null); }
  };

  const toggleTrigger = async (row) => {
    try { await adminApi.updateTrigger(row.id, { is_active: !row.is_active }); await load(); }
    catch (e) { notify(e.message, "err"); }
  };

  if (loading) return <p className="center muted">Loading…</p>;

  return (
    <div>
      <div className="row gap between">
        <div>
          <h1>Notification Settings</h1>
          <p className="muted">Row = trigger · column = channel · each cell = one template. Templates are managed only here.</p>
        </div>
        <button className="btn primary" onClick={() => setNewTrigger(true)}>+ New trigger</button>
      </div>

      <div className="table-wrap">
        <table className="matrix">
          <thead>
            <tr><th>Trigger</th>{CHANNELS.map((c) => <th key={c.key}>{c.label}</th>)}</tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className={row.is_active ? "" : "inactive"}>
                <td className="trigger-col">
                  <div className="row gap between">
                    <div>
                      <strong>{row.name}</strong>
                      <div className="muted small-text">{row.description}</div>
                      <code className="small-text">{row.key}</code>
                    </div>
                    <Switch checked={row.is_active} onChange={() => toggleTrigger(row)} label="Trigger active" />
                  </div>
                </td>
                {CHANNELS.map((c) => (
                  <td key={c.key}>
                    <MatrixCell
                      cell={row.cells[c.key]} channel={c.key} busy={busy === row.cells[c.key]?.id}
                      onCreate={() => setEditing({ trigger: row, channel: c.key })}
                      onEdit={() => setEditing({ trigger: row, channel: c.key, template: row.cells[c.key] })}
                      onToggle={() => toggle(row.cells[c.key])}
                      onTest={() => setTesting({ template: row.cells[c.key], channel: c.key })}
                    />
                  </td>
                ))}
              </tr>
            ))}
            {rows.length === 0 && <tr><td colSpan={4} className="center muted">No triggers yet.</td></tr>}
          </tbody>
        </table>
      </div>

      {editing && (
        <TemplateModal {...editing} variables={variables} notify={notify}
          onClose={() => setEditing(null)} onSaved={load} />
      )}
      {testing && <TestSendModal {...testing} notify={notify} onClose={() => { setTesting(null); }} />}
      {newTrigger && <NewTriggerModal notify={notify} onClose={() => setNewTrigger(false)} onCreated={load} />}
      <Toast toast={toast} />
    </div>
  );
}
