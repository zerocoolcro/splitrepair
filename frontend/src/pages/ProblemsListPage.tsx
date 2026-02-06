import { useEffect, useState } from "react";
import { fetchProblems } from "@/services/problems.service";

interface Problem {
  id: number;
  title: string;
  status: { name: string };
  created_at: string;
}

export default function ProblemsListPage() {
  const [problems, setProblems] = useState<Problem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProblems()
      .then((data) => setProblems(data.items))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-6">Loading...</div>;

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <h1 className="text-2xl font-semibold mb-4">Problemi u gradu</h1>

      <div className="grid gap-4">
        {problems.map((p) => (
          <div
            key={p.id}
            className="bg-white p-4 rounded-xl shadow flex justify-between"
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
          </div>
        ))}
      </div>
    </div>
  );
}
