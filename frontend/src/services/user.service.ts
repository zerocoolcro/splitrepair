import { api } from "./api";

export const fetchMe = async () => {
  const res = await api.get("/me");
  return res.data;
};
