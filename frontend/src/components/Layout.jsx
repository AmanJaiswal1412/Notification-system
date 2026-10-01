import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const onLogout = async () => { await logout(); navigate("/login"); };

  return (
    <div>
      <header className="topbar">
        <strong>🔔 Notify Demo</strong>
        <nav>
          <NavLink to="/" end>Website</NavLink>
          {user?.is_admin && <NavLink to="/admin" end>Notification Settings</NavLink>}
          {user?.is_admin && <NavLink to="/admin/logs">Send log</NavLink>}
        </nav>
        <span className="spacer" />
        {user && <span className="muted">{user.username}{user.is_admin ? " (admin)" : ""}</span>}
        {user && <button className="btn small" onClick={onLogout}>Log out</button>}
      </header>
      <main className="container"><Outlet /></main>
    </div>
  );
}
