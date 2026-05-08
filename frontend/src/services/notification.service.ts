const API = "http://127.0.0.1:8000";
const token = localStorage.getItem("token");

export const fetchNotifications = async () => {
  const res = await fetch(`${API}/notifications`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok) throw new Error("Greška kod fetch notifications");

  return res.json();
};

export const markAsRead = async (id: number) => {
  const res = await fetch(`${API}/notifications/${id}/read`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok) throw new Error("Greška kod mark as read");

  return res.json();
};
