import { request } from "./client.js";

export const authApi = {
  login: (username, password) => request("/api/auth/login/", { method: "POST", body: { username, password } }),
  register: (payload) => request("/api/auth/register/", { method: "POST", body: payload }),
  logout: () => request("/api/auth/logout/", { method: "POST" }),
  me: () => request("/api/auth/me/"),
  updatePhone: (phone) => request("/api/auth/me/", { method: "PATCH", body: { phone } }),
  passwordReset: (username) => request("/api/auth/password-reset/", { method: "POST", body: { username } }),
  pushSubscribe: (subscription_id) => request("/api/push/subscribe/", { method: "POST", body: { subscription_id } }),
};
