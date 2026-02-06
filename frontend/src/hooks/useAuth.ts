import { useEffect, useState } from "react";
import { authStore } from "@/store/auth.store";
import { fetchMe } from "@/services/auth.service";
import type { User } from "@/types/user";

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = authStore.token;

    if (!token) {
      setLoading(false);
      return;
    }

    fetchMe()
      .then((data) => setUser(data))
      .catch(() => authStore.logout())
      .finally(() => setLoading(false));
  }, [authStore.token]);

  return {
    user,
    loading,
    token: authStore.token,
    isLoggedIn: !!authStore.token,
    login: (token: string) => authStore.setToken(token),
    logout: () => authStore.logout(),
  };
};
