import { useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";

export default function Dashboard() {
  const { logout, user, loading } = useAuth();
  const navigate = useNavigate();

  if (loading) return <div className="p-6">Loading...</div>;

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="bg-white p-6 rounded-xl shadow flex justify-between items-center">
        <div>
          <h1 className="text-xl font-semibold">Dashboard</h1>

          {user && (
            <p className="text-gray-600 mt-1">
              Ulogiran kao: <b>{user.username}</b>
            </p>
          )}

          <button
            onClick={() => navigate("/problems")}
            className="text-left px-3 py-2 rounded hover:bg-gray-100"
          >
            🛠 Problemi
          </button>
        </div>

        <div className="flex items-center gap-3">
          {user?.role === "admin" && (
            <button
              onClick={() => navigate("/admin")}
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              Admin Panel
            </button>
          )}

          <button
            onClick={handleLogout}
            className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  );
}
