import { api } from "./api";

export const saveProblem = async (problemId: number) => {
  const res = await api.post(`/saved/${problemId}`);
  return res.data;
};

export const unsaveProblem = async (problemId: number) => {
  const res = await api.delete(`/saved/${problemId}`);
  return res.data;
};

export const fetchSavedProblems = async () => {
  const res = await api.get("/saved");
  return res.data;
};
