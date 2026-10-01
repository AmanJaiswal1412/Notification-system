import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function LoginPage() {
  const { user, login, register } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ username: "", password: "", email: "", first_name: "", phone: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  if (user) return <Navigate to={user.is_admin ? "/admin" : "/"} replace />;

  const submit = async (e) => {
    e.preventDefault(); setError(""); setBusy(true);
    try {
      const u = mode === "login" ? await login(form.username, form.password) : await register(form);
      navigate(u.is_admin ? "/admin" : "/");
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  };

  return (
    <div className="auth-wrap">
      <form className="card auth" onSubmit={submit}>
        <h1>🔔 Notify Demo</h1>
        <p className="muted">{mode === "login" ? "Sign in - this fires the Login trigger." : "Create a user account."}</p>
        <label>Username<input required value={form.username} onChange={(e) => set("username", e.target.value)} autoFocus /></label>
        {mode === "register" && (
          <>
            <label>First name<input value={form.first_name} onChange={(e) => set("first_name", e.target.value)} /></label>
            <label>Email<input required type="email" value={form.email} onChange={(e) => set("email", e.target.value)} /></label>
            <label>WhatsApp phone (country code, digits)<input value={form.phone} onChange={(e) => set("phone", e.target.value)} placeholder="919876543210" /></label>
          </>
        )}
        <label>Password<input required type="password" minLength={6} value={form.password} onChange={(e) => set("password", e.target.value)} /></label>
        {error && <p className="err">{error}</p>}
        <button className="btn primary wide" disabled={busy}>{busy ? "Please wait…" : mode === "login" ? "Log in" : "Register"}</button>
        <button type="button" className="link" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}>
          {mode === "login" ? "No account? Register" : "Have an account? Log in"}
        </button>
      </form>
    </div>
  );
}
