import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../utils/AuthContext.jsx";

export default function Topbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/login");
  }

  return (
    <header className="topbar">
      <div className="topbar-inner">
        <Link to={user ? (user.role === "teacher" ? "/teacher" : "/student") : "/"} style={{ textDecoration: "none" }}>
          <div className="wordmark">Coursework<span>Cloud</span></div>
        </Link>
        {user && (
          <div className="nav-actions">
            <span>{user.name} · {user.role}</span>
            <button className="secondary" onClick={handleLogout}>Log out</button>
          </div>
        )}
      </div>
    </header>
  );
}
