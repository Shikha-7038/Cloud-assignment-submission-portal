import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../services/api";
import { formatDate } from "../utils/format";
import StatusBadge from "../components/StatusBadge.jsx";

export default function GradeSubmission() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [submission, setSubmission] = useState(null);
  const [assignment, setAssignment] = useState(null);
  const [marks, setMarks] = useState("");
  const [feedback, setFeedback] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const s = await api.getSubmission(id);
        setSubmission(s);
        setMarks(s.marks ?? "");
        setFeedback(s.feedback ?? "");
        const a = await api.getAssignment(s.assignment_id);
        setAssignment(a);
      } catch (err) {
        setError(err.message);
      }
    }
    load();
  }, [id]);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await api.gradeSubmission(id, { marks: Number(marks), feedback });
      navigate(`/assignments/${submission.assignment_id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  if (!submission || !assignment) {
    return <div className="shell">{error ? <div className="error-banner">{error}</div> : "Loading…"}</div>;
  }

  return (
    <div className="shell">
      <h1>Review submission</h1>
      <p className="muted">{assignment.title} · {submission.file_name} · v{submission.version}</p>
      {error && <div className="error-banner">{error}</div>}

      <div className="split-columns">
        <section className="section">
          <h2>Submission</h2>
          <p><strong>Submitted:</strong> {formatDate(submission.submitted_at)}</p>
          <p><strong>Status:</strong> <StatusBadge status={submission.submission_status} /></p>
          <button className="secondary" onClick={() => api.downloadSubmission(submission.submission_id, submission.file_name)}>
            Download file to review
          </button>
        </section>

        <section className="section">
          <h2>Grade & feedback</h2>
          <form onSubmit={handleSubmit}>
            <div className="field">
              <label htmlFor="marks">Marks (out of {assignment.max_marks})</label>
              <input id="marks" type="number" min="0" max={assignment.max_marks} step="0.5" required
                     value={marks} onChange={(e) => setMarks(e.target.value)} />
            </div>
            <div className="field">
              <label htmlFor="feedback">Written feedback</label>
              <textarea id="feedback" rows={6} required value={feedback}
                        onChange={(e) => setFeedback(e.target.value)} />
            </div>
            <button type="submit" disabled={saving}>{saving ? "Saving…" : "Save grade"}</button>
          </form>
        </section>
      </div>
    </div>
  );
}
