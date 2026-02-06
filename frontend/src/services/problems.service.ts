import { api } from "@/services/api";

export const fetchProblems = async (page = 1, limit = 10) => {
  const res = await api.get(`/problems?page=${page}&limit=${limit}`);
  return res.data;
};
