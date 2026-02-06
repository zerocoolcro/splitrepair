import { Navigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";

interface AdminRouteProps {
  children: JSX.Element;
}

export const AdminRoute = ({ children }: AdminRouteProps) => {
  const { user, isLoggedIn, loading } = useAuth();

  if (loading) return <div className="p-6">Loading...</div>;

  // Ako nije ulogiran → login
  if (!isLoggedIn) return <Navigate to="/login" replace />;

  // Ako je ulogiran, ali nije admin → dashboard
  if (user?.role !== "admin") return <Navigate to="/dashboard" replace />;

  // Ako je admin → pusti dalje
  return children;
};
