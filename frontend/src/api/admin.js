import { request } from "./client.js";

export const adminApi = {
  triggers: () => request("/api/admin/triggers/"),
  createTrigger: (data) => request("/api/admin/triggers/", { method: "POST", body: data }),
  updateTrigger: (id, data) => request(`/api/admin/triggers/${id}/`, { method: "PATCH", body: data }),
  variables: () => request("/api/admin/variables/"),
  createTemplate: (data) => request("/api/admin/templates/", { method: "POST", body: data }),
  updateTemplate: (id, data) => request(`/api/admin/templates/${id}/`, { method: "PATCH", body: data }),
  toggleTemplate: (id, is_enabled) => request(`/api/admin/templates/${id}/toggle/`, { method: "POST", body: { is_enabled } }),
  testTemplate: (id, recipient) => request(`/api/admin/templates/${id}/test/`, { method: "POST", body: { recipient } }),
  submitTemplate: (id) => request(`/api/admin/templates/${id}/submit/`, { method: "POST" }),
  syncTemplate: (id) => request(`/api/admin/templates/${id}/sync/`, { method: "POST" }),
  logs: () => request("/api/admin/logs/"),
};
