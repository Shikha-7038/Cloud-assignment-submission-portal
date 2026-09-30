import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./utils/AuthContext.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import Topbar from "./components/Topbar.jsx";

import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import StudentDashboard from "./pages/StudentDashboard.jsx";
import TeacherDashboard from "./pages/TeacherDashboard.jsx";
import CreateAssignment from "./pages/CreateAssignment.jsx";
import AssignmentDetail from "./pages/AssignmentDetail.jsx";
import GradeSubmission from "./pages/GradeSubmission.jsx";

function Home() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return <Navigate to={user.role === "teacher" ? "/teacher" : "/student"} replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <Topbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route path="/student" element={
          <ProtectedRoute role="student"><StudentDashboard /></ProtectedRoute>
        } />

        <Route path="/teacher" element={
          <ProtectedRoute role="teacher"><TeacherDashboard /></ProtectedRoute>
        } />

        <Route path="/assignments/new" element={
          <ProtectedRoute role="teacher"><CreateAssignment /></ProtectedRoute>
        } />

        <Route path="/assignments/:id" element={
          <ProtectedRoute><AssignmentDetail /></ProtectedRoute>
        } />

        <Route path="/submissions/:id/grade" element={
          <ProtectedRoute role="teacher"><GradeSubmission /></ProtectedRoute>
        } />

        <Route path="*" element={
          <div className="shell"><h1>Page not found</h1></div>
        } />
      </Routes>
    </AuthProvider>
  );
}
