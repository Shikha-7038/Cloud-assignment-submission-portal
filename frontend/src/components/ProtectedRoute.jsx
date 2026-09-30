import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../utils/AuthContext.jsx";

/**
 * Client-side gate only. It stops a student from even seeing a teacher page
 * shell, but the REAL authorization boundary is enforced server-side by
 * @require_role on every API route - this component is a UX nicety, not a
 * security control, and must never be treated as one.
 */
export default function ProtectedRoute({ role, children }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (role && user.role !== role) {
    return <Navigate to={user.role === "teacher" ? "/teacher" : "/student"} replace />;
  }
  return children;
}
