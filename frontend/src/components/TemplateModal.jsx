import { useEffect, useMemo, useState } from "react";
import { adminApi } from "../api/admin.js";
import StatusBadge from "./StatusBadge.jsx";

const LABELS = { whatsapp: "WhatsApp", email: "Email", push: "Web Push" };
const PLACEHOLDER_RE = /\{\{\s*([\w.]+)\s*\}\}/g;

function placeholders(text) {
  const out = [];
  for (const m of (text || "").matchAll(PLACEHOLDER_RE)) if (!out.includes(m[1])) out.push(m[1]);
  return out;
}

export default function TemplateModal({ trigger, channel, template, variables, onClose, onSaved, notify }) {
  const isNew = !template;
  const [form, setForm] = useState(() => ({
    name: "", subject: "", title: "", body: "", url: "", variable_mapping: {},
    wa_template_name: "", wa_language: "en_US", wa_category: "UTILITY",
    ...(template || {}),
  }));
  const [saving, setSaving] = useState(false);
  const [working, setWorking] = useState("");
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const phs = useMemo(() => placeholders(`${form.subject} ${form.title} ${form.body}`), [form.subject, form.title, form.body]);
  useEffect(() => { document.body.style.overflow = "hidden"; return () => { document.body.style.overflow = ""; }; }, []);

  const save = async () => {
    setSaving(true);
    try {
      const payload = {
        name: form.name, subject: form.subject, title: form.title, body: form.body, url: form.url,
        variable_mapping: form.variable_mapping,
        wa_template_name: form.wa_template_name, wa_language: form.wa_language, wa_category: form.wa_category,
      };
      const saved = isNew
        ? await adminApi.createTemplate({ ...payload, trigger: trigger.id, channel, is_enabled: false })
        : await adminApi.updateTemplate(template.id, payload);
      notify("Template saved");
      onSaved(saved);
      return saved;
    } catch (e) { notify(e.message, "err"); return null; } finally { setSaving(false); }
  };

  const waAction = async (kind) => {
    const saved = await save();
    if (!saved) return;
    setWorking(kind);
    try {
      const fn = kind === "submit" ? adminApi.submitTemplate : adminApi.syncTemplate;
      const updated = await fn(saved.id);
      setForm((f) => ({ ...f, ...updated }));
      onSaved(updated);
      notify(kind === "submit" ? "Submitted to Meta" : `Status: ${updated.wa_status}`);
    } catch (e) { notify(e.message, "err"); } finally { setWorking(""); }
  };

  return (
    <div className="overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <h2>{isNew ? "Create" : "Edit"} {LABELS[channel]} template <span className="muted">· {trigger.name}</span></h2>

        <label>Internal name<input value={form.name} onChange={(e) => set("name", e.target.value)} placeholder="e.g. Login welcome" /></label>

        {channel === "email" && (
          <label>Subject<input value={form.subject} onChange={(e) => set("subject", e.target.value)} /></label>
        )}
        {channel === "push" && (
          <>
            <label>Title<input value={form.title} onChange={(e) => set("title", e.target.value)} /></label>
            <label>Click URL (optional)<input value={form.url} onChange={(e) => set("url", e.target.value)} placeholder="https://…" /></label>
          </>
        )}

        <label>
          Body
          <textarea rows={channel === "email" ? 7 : 4} value={form.body} onChange={(e) => set("body", e.target.value)}
            placeholder={channel === "whatsapp" ? "Hi {{1}}, welcome back to {{2}}!" : "Hi {{user.first_name}}, welcome back!"} />
        </label>
        <p className="hint">
          Use <code>{"{{placeholder}}"}</code>.
          {channel === "whatsapp" ? " WhatsApp requires numbered placeholders ({{1}}, {{2}}…) - map each one below." : " You can use a variable key directly, e.g. {{user.first_name}}."}
        </p>

        {phs.length > 0 && (
          <div className="mapping">
            <strong>Variable mapping</strong>
            {phs.map((p) => (
              <div className="row gap" key={p}>
                <code>{`{{${p}}}`}</code> →
                <select value={form.variable_mapping[p] || (p.includes(".") || p === "site_name" ? p : "")}
                  onChange={(e) => set("variable_mapping", { ...form.variable_mapping, [p]: e.target.value })}>
                  <option value="">(choose)</option>
                  {variables.map((v) => <option key={v.key} value={v.key}>{v.label} - {v.key}</option>)}
                </select>
              </div>
            ))}
          </div>
        )}

        {channel === "whatsapp" && (
          <div className="mapping">
            <div className="row gap wrap">
              <strong>WhatsApp approval</strong>
              <StatusBadge value={form.wa_status || "draft"} />
              {form.wa_rejection_reason && <span className="err">{form.wa_rejection_reason}</span>}
            </div>
            <div className="grid3">
              <label>Meta template name<input value={form.wa_template_name} onChange={(e) => set("wa_template_name", e.target.value)} placeholder="auto (or hello_world)" /></label>
              <label>Language<input value={form.wa_language} onChange={(e) => set("wa_language", e.target.value)} /></label>
              <label>Category
                <select value={form.wa_category} onChange={(e) => set("wa_category", e.target.value)}>
                  <option>UTILITY</option><option>MARKETING</option><option>AUTHENTICATION</option>
                </select>
              </label>
            </div>
            <p className="hint">Sandbox shortcut: name it <code>hello_world</code> and press Sync - it is pre-approved by Meta.</p>
            <div className="row gap">
              <button className="btn small" disabled={!!working} onClick={() => waAction("submit")}>{working === "submit" ? "Submitting…" : "Save & submit to Meta"}</button>
              <button className="btn small" disabled={!!working} onClick={() => waAction("sync")}>{working === "sync" ? "Syncing…" : "Sync status"}</button>
            </div>
          </div>
        )}

        <div className="row gap end">
          <button className="btn ghost" onClick={onClose}>Close</button>
          <button className="btn primary" disabled={saving} onClick={async () => { const s = await save(); if (s) onClose(); }}>
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}
