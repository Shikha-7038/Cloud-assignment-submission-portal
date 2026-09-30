import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";

export default function CreateAssignment() {
  const navigate = useNavigate();
  const [courses, setCourses] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    course_id: "", title: "", description: "", deadline: "", max_marks: 100,
    allowed_file_types: "pdf,docx", max_file_size_mb: 10, allow_resubmission: true, reject_late: false,
  });

  useEffect(() => {
    api.listCourses().then((c) => {
      setCourses(c);
      if (c.length > 0) setForm((f) => ({ ...f, course_id: c[0].course_id }));
    }).catch((err) => setError(err.message));
  }, []);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const deadlineIso = new Date(form.deadline).toISOString();
      const assignment = await api.createAssignment({ ...form, deadline: deadlineIso });
      navigate(`/assignments/${assignment.assignment_id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  if (courses.length === 0 && !error) {
    return (
      <div className="shell">
        <h1>New assignment</h1>
        <div className="section empty-state">
          You need a course before you can post an assignment. Go back to your dashboard and create one first.
        </div>
      </div>
    );
  }

  return (
    <div className="shell">
      <h1>New assignment</h1>
      <div className="section" style={{ maxWidth: 560 }}>
        {error && <div className="error-banner">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="course">Course</label>
            <select id="course" value={form.course_id} onChange={(e) => update("course_id", e.target.value)}>
              {courses.map((c) => <option key={c.course_id} value={c.course_id}>{c.course_name}</option>)}
            </select>
          </div>
          <div className="field">
            <label htmlFor="title">Title</label>
            <input id="title" required value={form.title} onChange={(e) => update("title", e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="description">Description</label>
            <textarea id="description" rows={4} value={form.description}
                      onChange={(e) => update("description", e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="deadline">Deadline</label>
            <input id="deadline" type="datetime-local" required value={form.deadline}
                   onChange={(e) => update("deadline", e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="max_marks">Maximum marks</label>
            <input id="max_marks" type="number" min="1" required value={form.max_marks}
                   onChange={(e) => update("max_marks", Number(e.target.value))} />
          </div>
          <div className="field">
            <label htmlFor="types">Allowed file types (comma-separated)</label>
            <input id="types" value={form.allowed_file_types}
                   onChange={(e) => update("allowed_file_types", e.target.value)} />
            <span className="muted">Supported: pdf, docx, zip, png, jpg, jpeg, txt</span>
          </div>
          <div className="field">
            <label htmlFor="max_size">Maximum file size (MB)</label>
            <input id="max_size" type="number" min="1" max="25" required value={form.max_file_size_mb}
                   onChange={(e) => update("max_file_size_mb", Number(e.target.value))} />
          </div>
          <div className="field" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <input id="resub" type="checkbox" style={{ width: "auto" }} checked={form.allow_resubmission}
                   onChange={(e) => update("allow_resubmission", e.target.checked)} />
            <label htmlFor="resub" style={{ margin: 0 }}>Allow resubmission</label>
          </div>
          <div className="field" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <input id="reject_late" type="checkbox" style={{ width: "auto" }} checked={form.reject_late}
                   onChange={(e) => update("reject_late", e.target.checked)} />
            <label htmlFor="reject_late" style={{ margin: 0 }}>Reject submissions after the deadline</label>
          </div>
          <button type="submit" disabled={loading}>{loading ? "Creating…" : "Create assignment"}</button>
        </form>
      </div>
    </div>
  );
}
