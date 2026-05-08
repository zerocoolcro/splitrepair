import { useEffect, useState } from "react";
import { fetchNotifications, markAsRead } from "@/services/notification.service";
import { useNavigate } from "react-router-dom";

type Notification = {
  id: number;
  message: string;
  read: boolean;
  created_at: string;
  problem_id?: number;   // 👈 DODANO
};

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadNotifications();
  }, []);

  const loadNotifications = async () => {
    setLoading(true);
    try {
      const data = await fetchNotifications();
      setNotifications(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRead = async (id: number) => {
    await markAsRead(id);
    setNotifications((prev) =>
      prev.map((n) =>
        n.id === id ? { ...n, read: true } : n
      )
    );
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex justify-between mb-6">
        <h1 className="text-2xl font-bold">🔔 Notifikacije</h1>

        <button
          onClick={() => navigate("/dashboard")}
          className="px-4 py-2 rounded bg-gray-200"
        >
          ← Natrag
        </button>
      </div>

      {loading && <p>Učitavanje...</p>}

      {!loading &&
        notifications.map((n) => (
          <div
            key={n.id}
            onClick={() => {
              if (n.problem_id) {
                navigate(`/problem/${n.problem_id}`);
              }
            }}
            className={`cursor-pointer border p-4 rounded mb-3 transition ${
              n.read ? "bg-gray-100" : "bg-white hover:shadow"
            }`}
          >
            <p className="font-medium">{n.message}</p>
            <p className="text-xs text-gray-500 mt-1">
              {new Date(n.created_at).toLocaleString()}
            </p>

            {!n.read && (
              <button
                onClick={(e) => {
                  e.stopPropagation();   // 👈 da ne triggera navigate
                  handleRead(n.id);
                }}
                className="text-sm text-blue-600 mt-2"
              >
                Označi kao pročitano
              </button>
            )}
          </div>
        ))}

      {!loading && notifications.length === 0 && (
        <p className="text-center text-gray-500 mt-6">
          Nema notifikacija.
        </p>
      )}
    </div>
  );
}
