import { useAuth } from "@/hooks/useAuth";

export default function AdminPage() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen p-6 bg-gray-100">
      <div className="bg-white p-6 rounded-xl shadow">
        <h1 className="text-xl font-semibold">Admin Panel</h1>
        <p className="mt-2 text-gray-600">
          Dobrodošao admin: <b>{user?.username}</b>
        </p>

        <div className="mt-6">
          <p>👮 Ovdje ide:</p>
          <ul className="list-disc ml-6 mt-2 text-sm text-gray-600">
            <li>Upravljanje korisnicima</li>
            <li>Brisanje / ban</li>
            <li>Admin statistika</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
