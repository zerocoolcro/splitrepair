import { useEffect, useState } from "react";
import { saveProblem, unsaveProblem, fetchSavedProblems } from "@/services/saved.service";
import { fetchNotifications } from "@/services/notification.service";
import { useNavigate } from "react-router-dom";
import SkeletonCard from "../components/SkeletonCard";

type Problem = {
  id: number;
  title: string;
  description: string;
  image_url?: string;
  created_at: string;
  status: { name: string };
  location?: {
    latitude?: number;
    longitude?: number;
    address?: string;
  };
};

export default function Dashboard() {
  const [problems, setProblems] = useState<Problem[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [role, setRole] = useState<string | null>(null);
  const [savedIds, setSavedIds] = useState<number[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const navigate = useNavigate();

  const token = localStorage.getItem("token");
  const username = localStorage.getItem("username");

  const fetchProblems = async () => {
    setLoading(true);
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/problems?search=${search}&status=${status}&page=${page}&limit=${limit}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      const data = await res.json();
      setProblems(data.items || []);
      setTotalPages(data.total_pages || 1);
    } catch (err) {
      console.error("Greška kod fetch problems:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProblems();
  }, [page, search, status]);

  useEffect(() => {
    fetchMe();
    loadSaved();
    loadNotifications();

    const handleNewProblem = () => fetchProblems();
    window.addEventListener("problemCreated", handleNewProblem);

    return () => window.removeEventListener("problemCreated", handleNewProblem);
  }, []);

  const fetchMe = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/me", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setRole(data.role);
    } catch (err) {
      console.error("Greška kod /me:", err);
    }
  };

  const loadSaved = async () => {
    try {
      const data = await fetchSavedProblems();
      setSavedIds(data.map((p: any) => p.id));
    } catch (err) {
      console.error("Greška kod fetchSavedProblems:", err);
    }
  };

  const loadNotifications = async () => {
    try {
      const data = await fetchNotifications();
      const unread = data.filter((n: any) => !n.read).length;
      setUnreadCount(unread);
    } catch (err) {
      console.error("Greška kod loadNotifications:", err);
    }
  };

  return (
    <div className="p-6">
      <div className="max-w-xl mx-auto">

        {/* HEADER */}
        <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4 mb-6">
          <div>
            <p className="text-sm text-gray-500">Prijavljen kao: </p>
            <p className="font-medium">{username}</p>
          </div>

          <div className="flex flex-wrap gap-3">
            {role === "admin" && (
              <button
                onClick={() => (window.location.href = "/admin")}
                className="px-4 py-2 rounded-lg bg-blue-600 text-white"
              >
                Admin Panel
              </button>
            )}

            <button
              onClick={() => (window.location.href = "/create-problem")}
              className="px-4 py-2 rounded-lg bg-green-600 text-white"
            >
              + Prijavi Problem
            </button>

            <button
              onClick={() => navigate("/map")}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
            >
              🗺 Pogledaj mapu
            </button>

            <button
              onClick={() => (window.location.href = "/saved")}
              className="px-4 py-2 rounded-lg bg-yellow-500 text-black"
            >
              ⭐ Saved ({savedIds.length})
            </button>

            <button
              onClick={() => (window.location.href = "/notifications")}
              className="relative px-4 py-2 rounded-lg bg-gray-800 text-white"
            >
              🔔
              {unreadCount > 0 && (
                <span className="absolute -top-2 -right-2 bg-red-500 text-xs text-white rounded-full px-2">
                  {unreadCount}
                </span>
              )}
            </button>

            <button
              onClick={() => {
                localStorage.removeItem("token");
                localStorage.removeItem("username");
                window.location.href = "/login";
              }}
              className="px-4 py-2 rounded-lg bg-red-500 text-white"
            >
              Logout
            </button>
          </div>
        </div>

        <h1 className="text-2xl font-bold mb-4">
          Prijavljeni problemi
        </h1>

        {/* FILTERS */}
        <div className="max-w-[800px] mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            <input
              type="text"
              placeholder="Pretraži..."
              value={search}
              onChange={(e) => {
                setPage(1);
                setSearch(e.target.value);
              }}
              className="border p-2 rounded w-full"
            />

            <select
              value={status}
              onChange={(e) => {
                setPage(1);
                setStatus(e.target.value);
              }}
              className="border p-2 rounded w-full md:w-40"
            >
              <option value="">Svi statusi</option>
              <option value="open">Open</option>
              <option value="pending">Pending</option>
              <option value="resolved">Resolved</option>
            </select>
          </div>
        </div>

        {/* LIST */}
        {loading && (
          <div className="grid gap-6 max-w-[800px]">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>
        )}

        {!loading &&
          problems.map((p) => {
            const statusColor =
              p.status.name === "open"
                ? "bg-red-500/10 text-red-600"
                : p.status.name === "pending"
                ? "bg-yellow-500/10 text-yellow-600"
                : "bg-green-500/10 text-green-600";

            return (
              <div
                key={p.id}
                onClick={() => {
                  if (
                      p.location?.latitude !== undefined &&
                      p.location?.longitude !== undefined
                  ) {
                    navigate("/map", {
                      state: {
                        lat: p.location.latitude,
                        lng: p.location.longitude,
                      },
                    });
                  }
                }}
                className="bg-white border rounded-xl p-4 mb-4 shadow-sm max-w-[800px] transition-all duration-300 hover:shadow-xl hover:-translate-y-1 cursor-pointer"
              >
                <div className="flex flex-col md:flex-row gap-4">
                  {p.image_url && (
                    <img
                      src={`http://127.0.0.1:8000${p.image_url}`}
                      className="w-full md:w-32 h-48 md:h-24 object-cover rounded-lg"
                    />
                  )}

                  <div className="flex-1">
                    <h2 className="text-lg font-semibold text-gray-800">
                      {p.title}
                    </h2>

                    <p className="text-sm text-gray-600 mt-1">
                      {p.description}
                    </p>

                    {p.location?.address && (
                      <p className="text-sm text-gray-500 mt-1">
                        📍 {p.location.address}
                      </p>
                    )}

                    <div className="flex justify-between items-center mt-3">
                      <div>
                        <p className="text-xs text-gray-400">
                          {new Date(p.created_at).toLocaleString()}
                        </p>

                        <span
                          className={`inline-block mt-1 text-xs font-semibold px-3 py-1 rounded-full ${statusColor}`}
                        >
                          {p.status.name.toUpperCase()}
                        </span>
                      </div>

                      <button
                        onClick={() => {
                          if (savedIds.includes(p.id)) {
                            unsaveProblem(p.id);
                            setSavedIds((prev) =>
                              prev.filter((id) => id !== p.id)
                            );
                          } else {
                            saveProblem(p.id);
                            setSavedIds((prev) => [...prev, p.id]);
                          }
                        }}
                        className="text-xl"
                      >
                        {savedIds.includes(p.id) ? "⭐" : "☆"}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}

        {!loading && problems.length === 0 && (
          <div className="text-center mt-20 space-y-4">
            <div className="text-6xl">🗺️</div>
            <h2 className="text-2xl font-semibold">Nema prijavljenih problema</h2>
            <p className="text-gray-500">
              Budi prvi koji će prijaviti problem u gradu.
            </p>
          </div>
        )}

        {/* PAGINATION */}
        <div className="flex flex-col md:flex-row justify-between items-center gap-4 mt-6 max-w-[800px]">
          <button
            onClick={() => setPage((p) => Math.max(p - 1, 1))}
            disabled={page === 1}
            className="px-4 py-2 rounded bg-gray-200 disabled:opacity-50"
          >
            Prev
          </button>

          <span className="text-sm">
            Stranica {page} / {totalPages}
          </span>

          <button
            onClick={() =>
              setPage((p) => Math.min(p + 1, totalPages))
            }
            disabled={page === totalPages}
            className="px-4 py-2 rounded bg-gray-200 disabled:opacity-50"
          >
            Next
          </button>
        </div>

      </div>
    </div>
  );
}
