import { useEffect, useState } from "react";
import { fetchProblems } from "@/services/problems.service";
import { Link } from "react-router-dom";

interface Problem {
  id: number;
  title: string;
  status: { name: string };
  created_at: string;
}

export default function ProblemsListPage() {
  const [problems, setProblems] = useState<Problem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");

  useEffect(() => {
    setLoading(true);
    fetchProblems({ search, status }).then((data) => {
      setProblems(data.items);
      setLoading(false);
    });
  }, [search, status]);

  if (loading) return <div className="p-6">Loading...</div>;

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <h1 className="text-2xl font-semibold mb-4">Problemi u gradu</h1>

      {/* FILTER BAR */}
      <div className="flex gap-3 mb-4">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Pretraži problem..."
          className="border rounded px-3 py-2 w-full"
        />

        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="border rounded px-3 py-2"
        >
          <option value="">Svi statusi</option>
          <option value="open">Open</option>
          <option value="pending">Pending</option>
          <option value="resolved">Resolved</option>
        </select>
      </div>

      <div className="grid gap-4">
        {problems.map((p) => (
          <Link
            key={p.id}
            to={`/problems/${p.id}`}
            className="bg-white p-4 rounded-xl shadow flex justify-between hover:bg-gray-50"
          >
            <div>
              <h2 className="font-semibold">{p.title}</h2>
              <p className="text-sm text-gray-500">
                {new Date(p.created_at).toLocaleDateString()}
              </p>
            </div>

            <span className="text-sm px-3 py-1 rounded bg-gray-200">
              {p.status.name}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}
