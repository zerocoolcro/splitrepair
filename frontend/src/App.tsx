import { BrowserRouter as Router, Routes, Route, Navigate, useLocation, useNavigate } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import Dashboard from "./pages/Dashboard";
import { ProtectedRoute } from "@/routes/ProtectedRoute";
import AdminPage from "./pages/AdminPage";
import { AdminRoute } from "@/routes/AdminRoute";
import ProblemsListPage from "@/pages/ProblemsListPage";
import ProblemDetail from "./pages/ProblemDetails";
import SavedPage from "@/pages/SavedPage";
import NotificationsPage from "./pages/NotificationsPage";
import CreateProblemPage from "./pages/CreateProblemPage"; 
import MapPage from "./pages/MapPage";
import { Home, Map, Bell } from "lucide-react";
import { Toaster } from "sonner";

function AppContent() {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <>
      <Toaster position="top-right" richColors />
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white">

        {/* NAVBAR */}
        <div className="sticky top-0 z-50 backdrop-blur-md bg-white/70 border-b border-white/40 shadow-sm">
          <div className="max-w-5xl mx-auto flex justify-between items-center px-6 py-3">

            <h1 className="text-xl font-bold text-gray-800">
              City Repair
            </h1>

            <div className="flex gap-6 items-center">

              {/* DASHBOARD */}
              <button
                onClick={() => navigate("/dashboard")}
                className={`relative flex items-center gap-2 px-3 py-2 transition ${
                  location.pathname === "/dashboard"
                    ? "text-blue-600"
                    : "text-gray-600 hover:text-blue-600"
                }`}
              >
                <Home size={18} />
                Dashboard

                {location.pathname === "/dashboard" && (
                  <span className="absolute left-0 -bottom-1 w-full h-[2px] bg-blue-600 rounded-full"></span>
                )}
              </button>

              {/* MAPA */}
              <button
                onClick={() => navigate("/map")}
                className={`relative flex items-center gap-2 px-3 py-2 transition ${
                  location.pathname === "/map"
                    ? "text-blue-600"
                    : "text-gray-600 hover:text-blue-600"
                }`}
              >
                <Map size={18} />
                Mapa

                {location.pathname === "/map" && (
                  <span className="absolute left-0 -bottom-1 w-full h-[2px] bg-blue-600 rounded-full"></span>
                )}
              </button>

              {/* NOTIFICATIONS */}
              <button
                onClick={() => navigate("/notifications")}
                className={`relative flex items-center gap-2 px-3 py-2 transition ${
                  location.pathname === "/notifications"
                    ? "text-blue-600"
                    : "text-gray-600 hover:text-blue-600"
                }`}
              >
                <Bell size={18} />
                Obavijesti

                {location.pathname === "/notifications" && (
                  <span className="absolute left-0 -bottom-1 w-full h-[2px] bg-blue-600 rounded-full"></span>
                )}
              </button>

            </div>
          </div>
        </div>

        {/* BACKGROUND BLOBS */}
        <div className="fixed inset-0 -z-10 overflow-hidden">
          <div className="absolute w-[400px] h-[400px] bg-blue-300 rounded-full blur-3xl opacity-30 animate-pulse top-[-100px] left-[-100px]" />
          <div className="absolute w-[400px] h-[400px] bg-purple-300 rounded-full blur-3xl opacity-30 animate-pulse bottom-[-100px] right-[-100px]" />
        </div>

        {/* ROUTES */}
        <Routes>
          <Route path="/" element={<Navigate to="/login" />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/problems" element={<ProblemsListPage />} />
          <Route path="/problems/:id" element={<ProblemDetail />} />
          <Route path="/saved" element={<SavedPage />} />
          <Route path="/notifications" element={<NotificationsPage />} />
          <Route path="/create-problem" element={<CreateProblemPage />} />
          <Route path="/map" element={<MapPage />} />

          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />

          <Route
            path="/admin"
            element={
              <AdminRoute>
                <AdminPage />
              </AdminRoute>
            }
          />
        </Routes>

      </div>
    </>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;