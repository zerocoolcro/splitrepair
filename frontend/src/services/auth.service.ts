import axios from "axios";

const API_URL = "http://127.0.0.1:8000";

export const loginRequest = async (username: string, password: string) => {
  const params = new URLSearchParams();
  params.append("username", username);
  params.append("password", password);

  const res = await axios.post(`${API_URL}/login`, params, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });

  return res.data;
};

export const registerRequest = async (username: string, password: string) => {
  const res = await axios.post(`${API_URL}/register`, {
    username,
    password,
  });

  return res.data;
};

// ✅ DODANO – dohvat trenutnog usera iz tokena
export const fetchMe = async () => {
  const token = localStorage.getItem("token");

  const res = await axios.get(`${API_URL}/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return res.data;
};
