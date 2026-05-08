import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  PieChart,
  Pie,
  Cell
} from "recharts";

type User = { id: number; username: string; role: string; };
type Problem = { id: number; title: string; description: string; status: string; user_id: number; image_url: string; location: string; };
type StatusHistory = { old_status: string; new_status: string; changed_by: string; changed_at: string; };

export default function AdminPage() {
  const navigate = useNavigate();
  const token = localStorage.getItem("token");

  const [users, setUsers] = useState<User[]>([]);
  const [problems, setProblems] = useState<Problem[]>([]);
  const [loading, setLoading] = useState(false);
  const [trend, setTrend] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);

  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");

  const headers = { Authorization: `Bearer ${token}` };
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  // ---------------- FETCHES ----------------

  const fetchTrend = async () => {
    const res = await fetch("http://127.0.0.1:8000/admin/problems/stats/trend", { headers });
    if (res.ok) setTrend(await res.json());
  };

  const fetchStats = async () => {
    const res = await fetch("http://127.0.0.1:8000/admin/problems/stats", { headers });
    if (res.ok) setStats(await res.json());
  };

  const loadUsers = async () => {
    const res = await fetch("http://127.0.0.1:8000/admin/users", { headers });
    if (res.ok) setUsers(await res.json());
  };

  const loadProblems = async () => {
    const res = await fetch("http://127.0.0.1:8000/admin/problems/", { headers });
    if (res.ok) setProblems(await res.json());
  };

  useEffect(() => {
    setLoading(true);
    Promise.all([
      loadUsers(),
      loadProblems(),
      fetchTrend(),
      fetchStats()
    ]).finally(() => setLoading(false));
  }, []);

  // ---------------- ACTIONS ----------------

  const deleteUser = async (id: number) => {
    if (!confirm("Obrisati korisnika?")) return;
    const res = await fetch(`http://127.0.0.1:8000/admin/users/${id}`, { method: "DELETE", headers });
    if (res.ok) loadUsers();
  };

  const deleteProblem = async (id: number) => {
    if (!confirm("Obrisati problem?")) return;
    const res = await fetch(`http://127.0.0.1:8000/admin/problems/${id}`, { method: "DELETE", headers });
    if (res.ok) loadProblems();
  };

  const updateStatus = async (id: number, newStatus: string) => {
    const res = await fetch(`http://127.0.0.1:8000/admin/problems/${id}/status`, {
      method: "PATCH",
      headers: { ...headers, "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus }),
    });
    if (res.ok) loadProblems();
    else alert("Greška kod update statusa.");
  };

  const bulkUpdateStatus = async (newStatus: string) => {
    if (!newStatus) return;

    if (selectedIds.length === 0) {
      alert("Nema odabranih problema.");
      return;
    }

    for (const id of selectedIds) {
      await fetch(`http://127.0.0.1:8000/admin/problems/${id}/status`, {
        method: "PATCH",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });
    }

    setSelectedIds([]);
    loadProblems();
  };

  const viewStatusHistory = async (id: number) => {
    const res = await fetch(`http://127.0.0.1:8000/admin/problems/${id}/status-history`, { headers });
    if (!res.ok) return alert("Greška kod dohvaćanja povijesti statusa.");
    const data: StatusHistory[] = await res.json();
    alert(JSON.stringify(data, null, 2));
  };

  const exportCSV = () => {
    const rows = [
      ["ID", "Title", "Status", "User ID"],
      ...problems.map(p => [p.id, p.title, p.status, p.user_id])
    ];

    const csvContent =
      "data:text/csv;charset=utf-8," +
      rows.map(e => e.join(",")).join("\n");

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "problems.csv");
    document.body.appendChild(link);
    link.click();
  };

  // ---------------- RENDER ----------------

  return (
    <div className="min-h-screen p-6 bg-gray-100">
      <div className="max-w-7xl mx-auto space-y-8">

        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold">🛠 Admin Dashboard</h1>
          <button onClick={() => navigate("/dashboard")} className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300">
            ← Natrag
          </button>
        </div>

        {loading && <p>Učitavanje...</p>}

        {/* KPI CARDS */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <Card
              title="Total"
              value={stats.total}
              subtitle={`${stats.growth >= 0 ? "↑" : "↓"} ${Math.abs(stats.growth)}% vs last week`}
              subtitleColor={stats.growth >= 0 ? "text-green-600" : "text-red-600"}
            />
            <Card title="Open" value={stats.open} color="text-red-500" />
            <Card title="Pending" value={stats.pending} color="text-yellow-500" />
            <Card title="Resolved" value={stats.resolved} color="text-green-600" />
            <Card title="Today" value={stats.today} color="text-indigo-600" />
          </div>
        )}

        {stats && (
          <div className="grid md:grid-cols-2 gap-6">

            {/* TOP USERS */}
            <div className="bg-white p-6 rounded-xl shadow">
              <h2 className="font-semibold mb-4">👤 Top korisnici</h2>
              {stats.top_users.map((u: any, index: number) => (
                <div key={index} className="flex justify-between border-b py-2">
                  <span>{u.username}</span>
                  <span className="font-semibold">{u.count}</span>
                </div>
              ))}
            </div>

            {/* TOP LOCATIONS */}
            <div className="bg-white p-6 rounded-xl shadow">
              <h2 className="font-semibold mb-4">📍 Najviše prijava</h2>
              {stats.top_locations.map((l: any, index: number) => (
                <div key={index} className="flex justify-between border-b py-2">
                  <span>{l.location}</span>
                  <span className="font-semibold">{l.count}</span>
                </div>
              ))}
            </div>

          </div>
        )}

        {/* USERS */}
        <div className="bg-white p-6 rounded-xl shadow">
          <h2 className="font-semibold mb-4">👥 Korisnici</h2>
          {users.map(u => (
            <div key={u.id} className="flex justify-between items-center border-b py-2">
              <div>{u.username} ({u.role})</div>
              {u.role !== "admin" && (
                <button onClick={() => deleteUser(u.id)} className="text-red-600 text-sm">
                  Delete
                </button>
              )}
            </div>
          ))}
        </div>

        {/* TREND */}

        <div className="bg-white p-6 rounded-xl shadow">
          <h2 className="font-semibold mb-6">📈 Problem Trend</h2>

          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tickFormatter={(value) => value.slice(5)} />
                <YAxis />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke="#6366f1"
                  strokeWidth={3}
                  dot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* STATUS DISTRIBUTION */}
        {stats && (
          <div className="bg-white p-6 rounded-xl shadow">
            <h2 className="font-semibold mb-6">📊 Status Distribution</h2>

            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={[
                      { name: "Open", value: stats.open },
                      { name: "Pending", value: stats.pending },
                      { name: "Resolved", value: stats.resolved }
                    ]}
                    dataKey="value"
                    outerRadius={100}
                    label
                  >
                    <Cell fill="#ef4444" />
                    <Cell fill="#eab308" />
                    <Cell fill="#16a34a" />
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

      {/* PROBLEMS */}
      <div className="bg-white p-6 rounded-xl shadow">
        <h2 className="font-semibold mb-4">🛠 Problemi</h2>

        <button
          onClick={exportCSV}
          className="mb-4 px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
        >
          📥 Export CSV
        </button>

        {/* SEARCH + FILTER */}
        <div className="flex gap-4 mb-6">
          <input
            type="text"
            placeholder="Search..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="border px-3 py-2 rounded w-full"
          />

          <select
            value={filterStatus}
            onChange={e => setFilterStatus(e.target.value)}
            className="border px-3 py-2 rounded"
          >
            <option value="all">All</option>
            <option value="open">Open</option>
            <option value="pending">Pending</option>
            <option value="resolved">Resolved</option>
          </select>
        </div>

        {/* BULK CONTROLS */}
        <div className="flex items-center gap-6 mb-4">
          <input
            type="checkbox"
            checked={selectedIds.length === problems.length && problems.length > 0}
            onChange={(e) => {
              if (e.target.checked) {
                setSelectedIds(problems.map(p => p.id));
              } else {
                setSelectedIds([]);
              }
            }}
          />
          <span className="text-sm">Select All</span>

          <select
            onChange={(e) => bulkUpdateStatus(e.target.value)}
            className="border p-2 rounded"
            defaultValue=""
          >
            <option value="" disabled>Change status</option>
            <option value="open">Open</option>
            <option value="pending">Pending</option>
            <option value="resolved">Resolved</option>
          </select>
        </div>

        {problems
          .filter(p => p.title.toLowerCase().includes(search.toLowerCase()))
          .filter(p => filterStatus === "all" ? true : p.status === filterStatus)
          .map(p => (
            <div key={p.id} className="border-b py-4 flex gap-4">

              {/* CHECKBOX */}
              <input
                type="checkbox"
                checked={selectedIds.includes(p.id)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedIds([...selectedIds, p.id]);
                  } else {
                    setSelectedIds(selectedIds.filter(id => id !== p.id));
                  }
                }}
              />

              <div className="flex-1 space-y-3">
                <div className="font-medium text-lg gap-2">{p.title}</div>

                {p.image_url && (
                  <img
                    src={`http://127.0.0.1:8000/${p.image_url}`}
                    alt="problem"
                    className="w-48 h-32 object-cover rounded"
                  />
                )}

                <div className="text-sm text-gray-600">{p.description}</div>

                <div className="flex items-center gap-2 text-xs">
                  <span className={`px-2 py-1 rounded-full text-white ${
                    p.status === "open"
                      ? "bg-red-500"
                      : p.status === "pending"
                      ? "bg-yellow-500"
                      : "bg-green-600"
                  }`}>
                    {p.status}
                  </span>
                </div>

                <span className="text-gray-500">User ID: {p.user_id}</span>

                <div className="flex items-center gap-3 mt-2">
                  <select
                    value={p.status}
                    onChange={e => updateStatus(p.id, e.target.value)}
                    className="border p-1 rounded"
                  >
                    <option value="open">open</option>
                    <option value="pending">pending</option>
                    <option value="resolved">resolved</option>
                  </select>

                  <button
                    onClick={() => deleteProblem(p.id)}
                    className="text-red-600 text-sm"
                  >
                    Delete
                  </button>

                  <button
                    onClick={() => viewStatusHistory(p.id)}
                    className="text-blue-600 text-sm"
                  >
                    Povijest statusa
                  </button>
                </div>
              </div>
            </div>
          ))}
      </div>
      </div>
    </div>
  );
}
   

// ---------------- COMPONENT ----------------

function Card({
  title,
  value,
  color = "",
  subtitle,
  subtitleColor = ""
}: {
  title: string;
  value: number;
  color?: string;
  subtitle?: string;
  subtitleColor?: string;
}) {
  return (
    <div className="bg-white p-4 rounded-xl shadow">
      <div className="text-sm text-gray-500">{title}</div>
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      {subtitle && (
        <div className={`text-xs mt-1 ${subtitleColor}`}>
          {subtitle}
        </div>
      )}
    </div>
  );
}