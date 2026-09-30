import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api";
import { formatDate } from "../utils/format";
import StatusBadge from "../components/StatusBadge.jsx";

export default function StudentDashboard() {
  const [dash, setDash] = useState(null);
  const [assignments, setAssignments] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const [d, a, s] = await Promise.all([
          api.studentDashboard(), api.listAssignments(), api.mySubmissions(),
        ]);
        setDash(d);
        setAssignments(a);
        setSubmissions(s);
      } catch (err) {
        setError(err.message);
      }
    }
    load();
  }, []);

  const latestByAssignment = {};
  for (const s of submissions) {
    const existing = latestByAssignment[s.assignment_id];
    if (!existing || s.version > existing.version) latestByAssignment[s.assignment_id] = s;
  }

  return (
    <div className="shell">
      <h1>My coursework</h1>
      {error && <div className="error-banner">{error}</div>}

      {dash && (
        <div className="stat-row">
          <div className="stat"><span className="n">{dash.total_assignments}</span><span className="label">Total</span></div>
          <div className="stat"><span className="n">{dash.pending_assignments}</span><span className="label">Pending</span></div>
          <div className="stat"><span className="n">{dash.submitted_assignments}</span><span className="label">Submitted</span></div>
          <div className="stat"><span className="n">{dash.late_assignments}</span><span className="label">Late</span></div>
          <div className="stat"><span className="n">{dash.graded_assignments}</span><span className="label">Graded</span></div>
        </div>
      )}

      <div className="split-columns">
        <section className="section">
          <h2>Assignments</h2>
          {assignments.length === 0 && <div className="empty-state">No assignments have been posted yet.</div>}
          {assignments.map((a) => {
            const sub = latestByAssignment[a.assignment_id];
            return (
              <div className="list-row" key={a.assignment_id}>
                <div className="list-row-main">
                  <div className="list-row-title">
                    <Link to={`/assignments/${a.assignment_id}`}>{a.title}</Link>
                  </div>
                  <div className="list-row-meta">Due {formatDate(a.deadline)}</div>
                </div>
                <StatusBadge status={sub ? sub.submission_status : "NOT_SUBMITTED"} />
              </div>
            );
          })}
        </section>

        <section className="section">
          <h2>Recent feedback</h2>
          {(!dash || dash.recent_feedback.length === 0) && (
            <div className="empty-state">Feedback will appear here once your work is graded.</div>
          )}
          {dash?.recent_feedback.map((f, i) => (
            <div className="list-row" key={i}>
              <div className="list-row-main">
                <div className="list-row-title">{f.assignment_title}</div>
                <div className="list-row-meta">{f.feedback}</div>
              </div>
              <strong>{f.marks}</strong>
            </div>
          ))}
        </section>
      </div>
    </div>
  );
}
