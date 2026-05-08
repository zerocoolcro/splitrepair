import axios from "axios";
import { authStore } from "@/store/auth.store";

const API_URL = "http://127.0.0.1:8000";

export const voteProblem = async (problemId: number, value: 1 | -1) => {
  const token = authStore.token;

  const res = await axios.post(
    `${API_URL}/votes/${problemId}`,
    { value },
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return res.data;
};
