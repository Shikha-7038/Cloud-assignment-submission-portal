import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api";
import { formatDate } from "../utils/format";

export default function TeacherDashboard() {
  const [dash, setDash] = useState(null);
  const [assignments, setAssignments] = useState([]);
  const [courses, setCourses] = useState([]);
  const [error, setError] = useState("");
  const [showNewCourse, setShowNewCourse] = useState(false);
  const [courseName, setCourseName] = useState("");

  async function load() {
    try {
      const [d, a, c] = await Promise.all([
        api.teacherDashboard(), api.listAssignments(), api.listCourses(),
      ]);
      setDash(d);
      setAssignments(a);
      setCourses(c);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleCreateCourse(e) {
    e.preventDefault();
    try {
      await api.createCourse({ course_name: courseName });
      setCourseName("");
      setShowNewCourse(false);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="shell">
      <div className="flex-between">
        <h1>Teaching overview</h1>
        <Link to="/assignments/new"><button>New assignment</button></Link>
      </div>
      {error && <div className="error-banner">{error}</div>}

      {dash && (
        <div className="stat-row">
          <div className="stat"><span className="n">{dash.total_assignments}</span><span className="label">Assignments</span></div>
          <div className="stat"><span className="n">{dash.total_students}</span><span className="label">Students</span></div>
          <div className="stat"><span className="n">{dash.total_submissions}</span><span className="label">Submissions</span></div>
          <div className="stat"><span className="n">{dash.pending_reviews}</span><span className="label">To review</span></div>
          <div className="stat"><span className="n">{dash.late_submissions}</span><span className="label">Late</span></div>
          <div className="stat"><span className="n">{dash.graded_submissions}</span><span className="label">Graded</span></div>
        </div>
      )}

      <div className="split-columns">
        <section className="section">
          <div className="flex-between">
            <h2>Courses</h2>
            <button className="link-btn" onClick={() => setShowNewCourse((v) => !v)}>
              {showNewCourse ? "Cancel" : "+ New course"}
            </button>
          </div>
          {showNewCourse && (
            <form onSubmit={handleCreateCourse} className="mt-1">
              <div className="field">
                <input placeholder="Course name, e.g. Cloud Computing 101" required
                       value={courseName} onChange={(e) => setCourseName(e.target.value)} />
              </div>
              <button type="submit">Create course</button>
            </form>
          )}
          {courses.length === 0 && !showNewCourse && (
            <div className="empty-state">Create a course before posting assignments.</div>
          )}
          {courses.map((c) => (
            <div className="list-row" key={c.course_id}>
              <div className="list-row-main">
                <div className="list-row-title">{c.course_name}</div>
                <div className="list-row-meta">Created {formatDate(c.created_at)}</div>
              </div>
            </div>
          ))}
        </section>

        <section className="section">
          <h2>Assignments</h2>
          {assignments.length === 0 && <div className="empty-state">No assignments yet.</div>}
          {assignments.map((a) => (
            <div className="list-row" key={a.assignment_id}>
              <div className="list-row-main">
                <div className="list-row-title">
                  <Link to={`/assignments/${a.assignment_id}`}>{a.title}</Link>
                </div>
                <div className="list-row-meta">Due {formatDate(a.deadline)} · Max {a.max_marks} marks</div>
              </div>
            </div>
          ))}
        </section>
      </div>
    </div>
  );
}
