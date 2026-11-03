const BASE = "/api";

async function request(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`فشل الطلب: ${res.status}`);
  return res.json();
}

export function getStats() {
  return request("/members/stats/");
}

export function getFamilies() {
  return request("/families/?page_size=200");
}

export function getMembers({ search = "", family = "", status = "", page = 1 } = {}) {
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (family) params.set("family", family);
  if (status) params.set("status", status);
  params.set("page", page);
  params.set("page_size", 25);
  return request(`/members/?${params.toString()}`);
}
