import React, { useEffect, useState, useCallback } from "react";
import { getStats, getFamilies, getMembers } from "./api";

const STATUS_TABS = [
  { value: "", label: "الكل" },
  { value: "عضو فاعل", label: "فاعل" },
  { value: "غير فاعل", label: "غير فاعل" },
  { value: "جديد", label: "جديد" },
];

function statusClass(status) {
  if (status === "عضو فاعل") return "active";
  if (status === "غير فاعل") return "inactive";
  return "new";
}

export default function App() {
  const [stats, setStats] = useState(null);
  const [families, setFamilies] = useState([]);
  const [selectedFamily, setSelectedFamily] = useState("");
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [members, setMembers] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getStats().then(setStats).catch(() => {});
    getFamilies().then((d) => setFamilies(d.results || [])).catch(() => {});
  }, []);

  const load = useCallback(() => {
    setLoading(true);
    getMembers({ search, family: selectedFamily, status, page })
      .then(setMembers)
      .catch(() => setMembers({ results: [], count: 0 }))
      .finally(() => setLoading(false));
  }, [search, selectedFamily, status, page]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    setPage(1);
  }, [search, selectedFamily, status]);

  const byStatus = Object.fromEntries(
    (stats?.by_status || []).map((s) => [s.status, s.count])
  );

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <h1>جمعية ديرابان الخيرية</h1>
          <p>سجل الأعضاء والاشتراكات</p>
        </div>

        <div className="stat-block">
          <div className="stat-row">
            <span>إجمالي الأعضاء</span>
            <span className="value">{stats?.total ?? "…"}</span>
          </div>
          <div className="stat-row active">
            <span>أعضاء فاعلون</span>
            <span className="value">{byStatus["عضو فاعل"] ?? "…"}</span>
          </div>
          <div className="stat-row inactive">
            <span>غير فاعلين</span>
            <span className="value">{byStatus["غير فاعل"] ?? "…"}</span>
          </div>
          <div className="stat-row new">
            <span>أعضاء جدد</span>
            <span className="value">{byStatus["جديد"] ?? "…"}</span>
          </div>
        </div>

        <nav className="family-list">
          <h2>العائلات ({families.length})</h2>
          <button
            className={`family-item ${selectedFamily === "" ? "selected" : ""}`}
            onClick={() => setSelectedFamily("")}
          >
            <span>كل العائلات</span>
          </button>
          {families
            .slice()
            .sort((a, b) => b.member_count - a.member_count)
            .map((f) => (
              <button
                key={f.id}
                className={`family-item ${selectedFamily === String(f.id) ? "selected" : ""}`}
                onClick={() => setSelectedFamily(String(f.id))}
              >
                <span>{f.name}</span>
                <span className="count">{f.member_count}</span>
              </button>
            ))}
        </nav>
      </aside>

      <main className="main">
        <div className="toolbar">
          <div className="search-box">
            <input
              type="text"
              placeholder="ابحث بالاسم أو رقم العضوية…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="status-tabs">
            {STATUS_TABS.map((t) => (
              <button
                key={t.value}
                className={status === t.value ? "selected" : ""}
                onClick={() => setStatus(t.value)}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        <div className="table-wrap">
          {loading ? (
            <div className="empty-state">جارٍ التحميل…</div>
          ) : !members || members.results.length === 0 ? (
            <div className="empty-state">لا يوجد أعضاء مطابقون لهذا البحث</div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>رقم العضوية</th>
                  <th>الاسم</th>
                  <th>العائلة</th>
                  <th>الحالة</th>
                  <th>2025</th>
                  <th>2024</th>
                  <th>2023</th>
                  <th>2022</th>
                  <th>2021</th>
                  <th>2020</th>
                  <th>أساس 2019</th>
                </tr>
              </thead>
              <tbody>
                {members.results.map((m) => (
                  <tr key={m.id}>
                    <td>{m.membership_number}</td>
                    <td>{m.full_name}</td>
                    <td>{m.family_name}</td>
                    <td>
                      <span className={`badge ${statusClass(m.status)}`}>{m.status}</span>
                    </td>
                    <td>{m.sub_2025 || "—"}</td>
                    <td>{m.sub_2024 || "—"}</td>
                    <td>{m.sub_2023 || "—"}</td>
                    <td>{m.sub_2022 || "—"}</td>
                    <td>{m.sub_2021 || "—"}</td>
                    <td>{m.sub_2020 || "—"}</td>
                    <td>{m.sub_2019_base || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {members && members.count > 0 && (
          <div className="pager">
            <span>
              {members.count} عضو — صفحة {page}
            </span>
            <div style={{ display: "flex", gap: 8 }}>
              <button disabled={!members.previous} onClick={() => setPage((p) => p - 1)}>
                السابق
              </button>
              <button disabled={!members.next} onClick={() => setPage((p) => p + 1)}>
                التالي
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
