import { useEffect, useState } from "react";
import { adminApi } from "../api/admin.js";
import StatusBadge from "../components/StatusBadge.jsx";

export default function LogsPage() {
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState("");
  const load = () => adminApi.logs().then(setLogs).catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);

  return (
    <div>
      <div className="row gap between">
        <div><h1>Send log</h1><p className="muted">Latest 200 attempts, including test sends.</p></div>
        <button className="btn" onClick={load}>Refresh</button>
      </div>
      {error && <p className="err">{error}</p>}
      <div className="table-wrap">
        <table className="matrix logs">
          <thead><tr><th>When</th><th>Trigger</th><th>Channel</th><th>User</th><th>Recipient</th><th>Status</th><th>Detail</th></tr></thead>
          <tbody>
            {logs.map((l) => (
              <tr key={l.id}>
                <td>{new Date(l.created_at).toLocaleString()}</td>
                <td>{l.trigger_key}{l.is_test && <span className="badge pending">test</span>}</td>
                <td>{l.channel}</td><td>{l.username}</td><td className="wrap-any">{l.recipient}</td>
                <td><StatusBadge value={l.status} /></td><td className="wrap-any">{l.detail}</td>
              </tr>
            ))}
            {logs.length === 0 && <tr><td colSpan={7} className="center muted">Nothing sent yet.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
