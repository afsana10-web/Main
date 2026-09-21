/* PARAKH Dashboard - API client
   All calls go through FastAPI. The dashboard NEVER talks to PostgreSQL
   directly. */

const API = (() => {
  // Adjust this if the backend runs on a different host/port.
  const BASE_URL = window.PARAKH_API_BASE || "http://localhost:8000";

  function getToken() {
    return sessionStorage.getItem("parakh_token");
  }

  function setToken(token) {
    sessionStorage.setItem("parakh_token", token);
  }

  function clearToken() {
    sessionStorage.removeItem("parakh_token");
  }

  async function request(path, { method = "GET", body, isForm = false, raw = false } = {}) {
    const headers = {};
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
    if (!isForm && body !== undefined) headers["Content-Type"] = "application/json";

    const res = await fetch(`${BASE_URL}${path}`, {
      method,
      headers,
      body: isForm ? body : (body !== undefined ? JSON.stringify(body) : undefined),
    });

    if (res.status === 401) {
      clearToken();
      Router.go("login");
      throw new Error("Session expired. Please log in again.");
    }

    if (raw) return res;

    const contentType = res.headers.get("content-type") || "";
    const data = contentType.includes("application/json") ? await res.json() : await res.text();

    if (!res.ok) {
      const message = (data && data.detail) ? data.detail : `Request failed (${res.status})`;
      throw new Error(typeof message === "string" ? message : JSON.stringify(message));
    }
    return data;
  }

  return {
    BASE_URL,
    getToken, setToken, clearToken,

    login: (officer_id, password) => request("/api/auth/login", { method: "POST", body: { officer_id, password } }),
    me: () => request("/api/auth/me"),

    dashboardStats: () => request("/api/dashboard/stats"),

    listInspections: (params = {}) => {
      const q = new URLSearchParams(Object.entries(params).filter(([, v]) => v));
      return request(`/api/inspections${q.toString() ? "?" + q.toString() : ""}`);
    },
    getInspection: (id) => request(`/api/inspections/${id}`),
    createInspection: (payload) => request("/api/inspections", { method: "POST", body: payload }),
    uploadImages: (id, formData) => request(`/api/inspections/${id}/images`, { method: "POST", body: formData, isForm: true }),
    analyzeInspection: (id) => request(`/api/inspections/${id}/analyze`, { method: "POST" }),
    getResults: (id) => request(`/api/inspections/${id}/results`),
    getFindings: (id) => request(`/api/inspections/${id}/findings`),
    getEvidence: (id) => request(`/api/inspections/${id}/evidence`),

    verifyFinding: (findingId, payload) => request(`/api/findings/${findingId}/verify`, { method: "POST", body: payload }),

    generateReport: (inspectionId) => request(`/api/reports/${inspectionId}/generate`, { method: "POST" }),
    downloadReportUrl: (reportId) => `${BASE_URL}/api/reports/${reportId}/download`,

    listRules: () => request("/api/rules"),
    createRule: (payload) => request("/api/rules", { method: "POST", body: payload }),
    updateRule: (id, payload) => request(`/api/rules/${id}`, { method: "PUT", body: payload }),
    deactivateRule: (id) => request(`/api/rules/${id}`, { method: "DELETE" }),

    listUsers: () => request("/api/users"),
    createUser: (payload) => request("/api/users", { method: "POST", body: payload }),
    updateUser: (id, payload) => request(`/api/users/${id}`, { method: "PUT", body: payload }),
    deactivateUser: (id) => request(`/api/users/${id}`, { method: "DELETE" }),

    demoCases: () => request("/api/demo/cases"),
    runDemoCase: (key) => request(`/api/demo/${key}/run`, { method: "POST" }),

    imageUrl: (path) => {
      // original_path is a server filesystem path like uploads/inspection_1/x.jpg
      // Map it to the /uploads static mount.
      const marker = "uploads/";
      const idx = path.indexOf(marker);
      const rel = idx >= 0 ? path.slice(idx + marker.length) : path;
      return `${BASE_URL}/uploads/${rel}`;
    },
  };
})();
