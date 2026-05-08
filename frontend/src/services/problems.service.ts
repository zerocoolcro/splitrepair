import { api } from "./api";

export const fetchProblems = async ({
  search = "",
  status = "",
  page = 1,
  limit = 10,
}: {
  search?: string;
  status?: string;
  page?: number;
  limit?: number;
}) => {
  const res = await api.get("/problems", {
    params: {
      q: search,
      status,
      page,
      limit,
    },
  });

  return res.data;
};

export const fetchProblemById = async (id: string) => {
  const res = await api.get(`/problems/${id}`);
  return res.data;
};

export const fetchComments = async (id: string) => {
  const res = await api.get(`/problems/${id}/comments`);
  return res.data;
};

export const postComment = async (id: string, content: string) => {
  const res = await api.post(`/problems/${id}/comments`, { content });
  return res.data;
};

export const createProblem = async (formData: FormData) => {
  const res = await api.post("/problems", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return res.data;
};
