// هذه الطبقة مخصّصة لأدوات سجل الأعضاء الإدارية، ومساراتها محمية بصلاحيات الإدارة.
const API_ROOT = import.meta.env.VITE_API_URL || "/api";
const BASE = API_ROOT.endsWith("/api") ? API_ROOT : `${API_ROOT.replace(/\/$/, "")}/api`;

async function request(path) {
  const token = localStorage.getItem("access");
  const response = await fetch(`${BASE}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) throw new Error(`فشل الطلب: ${response.status}`);
  return response.json();
}

export function getStats() {
  return request("/registry/members/stats/");
}

export function getFamilies() {
  return request("/registry/families/?page_size=200");
}

export function getMembers({ search = "", family = "", status = "", page = 1 } = {}) {
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (family) params.set("family", family);
  if (status) params.set("status", status);
  params.set("page", page);
  params.set("page_size", 25);
  return request(`/registry/members/?${params.toString()}`);
}
