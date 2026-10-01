import { useState } from "react";
import { adminApi } from "../api/admin.js";

export default function TestSendModal({ template, channel, onClose, notify }) {
  const [recipient, setRecipient] = useState("");
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState(null);

  const hint = {
    whatsapp: "Phone with country code (must be on your Meta test recipient list). Empty = your own profile phone.",
    email: "Email address. Empty = your own account email.",
    push: "Sent to browsers you subscribed with on the Website page.",
  }[channel];

  const send = async () => {
    setSending(true); setResult(null);
    try {
      const log = await adminApi.testTemplate(template.id, channel === "push" ? "" : recipient);
      setResult({ ok: true, text: log.detail });
      notify("Test sent");
    } catch (e) { setResult({ ok: false, text: e.data?.detail || e.message }); }
    finally { setSending(false); }
  };

  return (
    <div className="overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal small">
        <h2>Test send · {channel}</h2>
        {channel !== "push" && (
          <label>Recipient<input value={recipient} onChange={(e) => setRecipient(e.target.value)} placeholder={channel === "email" ? "you@example.com" : "919876543210"} /></label>
        )}
        <p className="hint">{hint}</p>
        {result && <p className={result.ok ? "ok" : "err"}>{result.ok ? "✓ " : "✗ "}{result.text}</p>}
        <div className="row gap end">
          <button className="btn ghost" onClick={onClose}>Close</button>
          <button className="btn primary" disabled={sending} onClick={send}>{sending ? "Sending…" : "Send test"}</button>
        </div>
      </div>
    </div>
  );
}
