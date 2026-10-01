import { useState } from "react";
import { adminApi } from "../api/admin.js";

export default function NewTriggerModal({ onClose, onCreated, notify }) {
  const [form, setForm] = useState({ name: "", key: "", description: "", inactivity_days: "" });
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const slug = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");

  const save = async () => {
    try {
      const created = await adminApi.createTrigger({
        name: form.name, key: form.key || slug(form.name), description: form.description,
        inactivity_days: form.inactivity_days ? Number(form.inactivity_days) : null,
      });
      notify("Trigger added");
      onCreated(created);
      onClose();
    } catch (e) { notify(e.message, "err"); }
  };

  return (
    <div className="overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal small">
        <h2>New trigger</h2>
        <label>Name<input value={form.name} onChange={(e) => set("name", e.target.value)} placeholder="Order placed" /></label>
        <label>Key (used in code)<input value={form.key} onChange={(e) => set("key", e.target.value)} placeholder={slug(form.name) || "order_placed"} /></label>
        <label>Description<input value={form.description} onChange={(e) => set("description", e.target.value)} /></label>
        <label>Inactivity days (optional)<input type="number" min="1" value={form.inactivity_days} onChange={(e) => set("inactivity_days", e.target.value)} /></label>
        <p className="hint">Inactivity triggers fire automatically via the daily scheduled job. Other triggers fire when backend code calls <code>fire_trigger("{form.key || slug(form.name) || "key"}", user)</code>.</p>
        <div className="row gap end">
          <button className="btn ghost" onClick={onClose}>Cancel</button>
          <button className="btn primary" disabled={!form.name} onClick={save}>Add</button>
        </div>
      </div>
    </div>
  );
}
