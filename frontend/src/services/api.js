/**
 * Thin fetch wrapper. Vite's dev proxy (see vite.config.js) forwards /api/*
 * to the Flask backend, so this code never needs to know its host/port.
 *
 * Every call attaches the JWT from localStorage as a Bearer token. The
 * backend is the only place that ever verifies that token - the frontend
 * just carries it back and forth.
 */
const TOKEN_KEY = "portal_token";
const USER_KEY = "portal_user";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser() {
  const raw = localStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}

export function saveSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

class ApiError extends Error {
  constructor(message, code, status) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

async function request(path, { method = "GET", body, isForm = false } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (body && !isForm) headers["Content-Type"] = "application/json";

  const res = await fetch(`/api${path}`, {
    method,
    headers,
    body: isForm ? body : body ? JSON.stringify(body) : undefined,
  });

  const isJson = res.headers.get("content-type")?.includes("application/json");

  if (!res.ok) {
    const data = isJson ? await res.json().catch(() => null) : null;
    const message = data?.error?.message || `Request failed (${res.status})`;
    const code = data?.error?.code || "UNKNOWN_ERROR";
    if (res.status === 401) {
      clearSession();
    }
    throw new ApiError(message, code, res.status);
  }

  if (isJson) return res.json();
  return res.blob();
}

export const api = {
  register: (data) => request("/register", { method: "POST", body: data }),
  login: (data) => request("/login", { method: "POST", body: data }),
  logout: () => request("/logout", { method: "POST" }),

  createCourse: (data) => request("/courses", { method: "POST", body: data }),
  listCourses: () => request("/courses"),

  createAssignment: (data) => request("/assignments", { method: "POST", body: data }),
  listAssignments: (courseId) => request(courseId ? `/assignments?course_id=${courseId}` : "/assignments"),
  getAssignment: (id) => request(`/assignments/${id}`),
  updateAssignment: (id, data) => request(`/assignments/${id}`, { method: "PUT", body: data }),
  deleteAssignment: (id) => request(`/assignments/${id}`, { method: "DELETE" }),

  submitAssignment: (assignmentId, file) => {
    const form = new FormData();
    form.append("file", file);
    return request(`/assignments/${assignmentId}/submit`, { method: "POST", body: form, isForm: true });
  },
  mySubmissions: () => request("/submissions/me"),
  submissionsForAssignment: (assignmentId) => request(`/assignments/${assignmentId}/submissions`),
  getSubmission: (id) => request(`/submissions/${id}`),
  downloadSubmission: async (id, filename) => {
    const blob = await request(`/submissions/${id}/download`);
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename || "submission";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  },

  gradeSubmission: (id, data) => request(`/submissions/${id}/grade`, { method: "POST", body: data }),
  getFeedback: (id) => request(`/submissions/${id}/feedback`),

  studentDashboard: () => request("/dashboard/student"),
  teacherDashboard: () => request("/dashboard/teacher"),
};

export { ApiError };
