import { useEffect, useState } from "react";
import { fetchSavedProblems, unsaveProblem } from "@/services/saved.service";

type Problem = {
  id: number;
  title: string;
  description: string;
  status: string;
  created_at: string;
};

export default function SavedPage() {
  const [saved, setSaved] = useState<Problem[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadSaved();
  }, []);

  const loadSaved = async () => {
    setLoading(true);
    try {
      const data = await fetchSavedProblems();
      setSaved(data || []);
    } catch (err) {
      console.error("Greška kod fetchSavedProblems:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">⭐ Saved problemi</h1>

        <button
          onClick={() => (window.location.href = "/dashboard")}
          className="px-4 py-2 rounded bg-gray-200"
        >
          ← Natrag na Dashboard
        </button>
      </div>

      {loading && <p>Učitavanje...</p>}

      {!loading &&
        saved.map((p) => (
          <div key={p.id} className="border p-4 rounded mb-3 hover:shadow transition">
            <h2 className="font-semibold">{p.title}</h2>
            <p className="text-sm text-gray-600">{p.description}</p>
            <p className="text-xs text-gray-500 mt-1">
              Status: {p.status} • {new Date(p.created_at).toLocaleString()}
            </p>

            <button
              onClick={() => {
                unsaveProblem(p.id);
                setSaved((prev) => prev.filter((x) => x.id !== p.id));
              }}
              className="text-sm text-red-500 mt-2"
            >
              ❌ Makni iz Saved
            </button>
          </div>
        ))}

      {!loading && saved.length === 0 && (
        <p className="text-sm text-gray-500 text-center mt-6">
          Nemaš spremljenih problema ⭐
        </p>
      )}
    </div>
  );
}
