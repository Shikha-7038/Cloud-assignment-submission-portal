import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../services/api";
import { useAuth } from "../utils/AuthContext.jsx";
import { formatDate, isPast } from "../utils/format";
import StatusBadge from "../components/StatusBadge.jsx";

export default function AssignmentDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const [assignment, setAssignment] = useState(null);
  const [submissions, setSubmissions] = useState([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  async function load() {
    try {
      const a = await api.getAssignment(id);
      setAssignment(a);
      if (user.role === "student") {
        const mine = await api.mySubmissions();
        setSubmissions(mine.filter((s) => s.assignment_id === id));
      } else {
        const all = await api.submissionsForAssignment(id);
        setSubmissions(all);
      }
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => { load(); }, [id]);

  async function handleUpload(e) {
    e.preventDefault();
    if (!file) return;
    setError("");
    setNotice("");
    setUploading(true);
    try {
      await api.submitAssignment(id, file);
      setNotice("Assignment submitted successfully.");
      setFile(null);
      e.target.reset();
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  if (!assignment) {
    return <div className="shell">{error ? <div className="error-banner">{error}</div> : "Loading…"}</div>;
  }

  const latest = submissions.length > 0
    ? submissions.reduce((a, b) => (a.version > b.version ? a : b))
    : null;
  const deadlinePassed = isPast(assignment.deadline);

  return (
    <div className="shell">
      <h1>{assignment.title}</h1>
      <p className="muted">
        Due {formatDate(assignment.deadline)} · Max {assignment.max_marks} marks
        {deadlinePassed && !assignment.reject_late && " · deadline has passed (late submissions accepted)"}
        {deadlinePassed && assignment.reject_late && " · deadline has passed (submissions closed)"}
      </p>
      {assignment.description && <p>{assignment.description}</p>}
      {error && <div className="error-banner">{error}</div>}
      {notice && <div className="success-banner">{notice}</div>}

      {user.role === "student" && (
        <section className="section">
          <h2>{latest ? "Resubmit" : "Submit your work"}</h2>
          <p className="muted">
            Accepted types: {assignment.allowed_file_types.split(",").join(", ")} · up to {assignment.max_file_size_mb} MB
          </p>
          {(!latest || assignment.allow_resubmission) && !(deadlinePassed && assignment.reject_late) ? (
            <form onSubmit={handleUpload}>
              <div className="field">
                <input type="file" required onChange={(e) => setFile(e.target.files[0])} />
              </div>
              <button type="submit" disabled={uploading}>{uploading ? "Uploading…" : "Upload"}</button>
            </form>
          ) : (
            <p className="muted">
              {deadlinePassed && assignment.reject_late
                ? "This assignment no longer accepts submissions."
                : "You have already submitted and resubmission is not allowed for this assignment."}
            </p>
          )}
        </section>
      )}

      <section className="section">
        <h2>{user.role === "student" ? "Your submissions" : "Student submissions"}</h2>
        {submissions.length === 0 && <div className="empty-state">No submissions yet.</div>}
        {submissions
          .slice()
          .sort((a, b) => b.version - a.version)
          .map((s) => (
            <div className="list-row" key={s.submission_id}>
              <div className="list-row-main">
                <div className="list-row-title">
                  {s.file_name} <span className="muted">v{s.version}</span>
                </div>
                <div className="list-row-meta">
                  Submitted {formatDate(s.submitted_at)}
                  {s.marks !== null && s.marks !== undefined && ` · ${s.marks}/${assignment.max_marks}`}
                </div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                <StatusBadge status={s.submission_status} />
                <button className="secondary" onClick={() => api.downloadSubmission(s.submission_id, s.file_name)}>
                  Download
                </button>
                {user.role === "teacher" && (
                  <Link to={`/submissions/${s.submission_id}/grade`}><button>Review</button></Link>
                )}
              </div>
            </div>
          ))}
      </section>
    </div>
  );
}
