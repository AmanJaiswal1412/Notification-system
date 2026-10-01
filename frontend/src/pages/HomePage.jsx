import { useState } from "react";
import { authApi } from "../api/auth.js";
import Toast from "../components/Toast.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { pushConfigured, subscribeToPush } from "../lib/push.js";
import { useToast } from "../lib/useToast.js";

// The "website": where users can trigger notifications (login/logout happen via the top bar & login page).
export default function HomePage() {
  const { user, setUser } = useAuth();
  const [toast, notify] = useToast();
  const [phone, setPhone] = useState(user.phone || "");
  const [subscribing, setSubscribing] = useState(false);
  const [subscribed, setSubscribed] = useState(false);
  const [resetBusy, setResetBusy] = useState(false);


  const savePhone = async () => {
    try { setUser(await authApi.updatePhone(phone)); notify("Phone saved"); } catch (e) { notify(e.message, "err"); }
  };

  const enablePush = async () => {
    setSubscribing(true);
    try {
      const id = await subscribeToPush();
      await authApi.pushSubscribe(id);
      setSubscribed(true);
      notify("Browser subscribed to Web Push");
    } catch (e) { notify(e.message, "err"); } finally { setSubscribing(false); }
  };

  const requestReset = async () => {
    setResetBusy(true);
    try { await authApi.passwordReset(user.username); notify("Password-reset trigger fired"); } catch (e) { notify(e.message, "err"); } finally { setResetBusy(false); }
  };

  return (
    <div className="stack">
      <div className="card">
        <h1>Hello, {user.first_name || user.username} 👋</h1>
        <p className="muted">
          You are signed in, so the <b>Login</b> trigger already fired. Press <b>Log out</b> (top right) to fire <b>Logout</b>.
          {user.is_admin && " Configure what gets sent under Notification Settings."}
        </p>
      </div>

      <div className="card">
        <h2>1 · WhatsApp number</h2>
        <p className="muted">Used for WhatsApp notifications. In sandbox it must be on your Meta test-recipient list.</p>
        <div className="row gap">
          <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="919876543210" />
          <button className="btn" onClick={savePhone}>Save</button>
        </div>
      </div>

      <div className="card">
        <h2>2 · Web Push</h2>
        <p className="muted">Subscribe this browser so it can receive pop-up notifications.</p>
        {!pushConfigured() && <p className="err">Set VITE_ONESIGNAL_APP_ID in the frontend env to enable push.</p>}
        <button className="btn primary" disabled={!pushConfigured() || subscribing} onClick={enablePush}>
          {subscribing ? "Subscribing…" : subscribed ? "✓ Subscribed (tap to refresh)" : "Enable Web Push"}
        </button>
      </div>

      <div className="card">
        <h2>3 · More triggers</h2>
        <p className="muted">Fire another website event manually.</p>
        <button className="btn" disabled={resetBusy} onClick={requestReset}>Request password reset</button>
      </div>
      <Toast toast={toast} />
    </div>
  );
}
