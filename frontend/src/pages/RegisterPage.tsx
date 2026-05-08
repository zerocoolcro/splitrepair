import { useState } from "react";
import { registerRequest } from "../services/auth.service";
import { useNavigate } from "react-router-dom";

export default function RegisterPage() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await registerRequest(username, password, firstName, lastName, email);
      alert("Registracija uspješna. Možeš se logirati.");
      navigate("/login");
    } catch (err) {
      alert("Greška kod registracije");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center">
      <form onSubmit={handleSubmit} className="bg-white p-6 rounded-xl shadow w-80">
        <h2 className="text-xl mb-4">Register</h2>
        <input
          className="border p-2 w-full mb-2"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <input
          className="border p-2 w-full mb-2"
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <input
          className="border p-2 w-full mb-4"
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <input
          className="border p-2 w-full mb-4"
          placeholder="Ime"
          value={firstName}
          onChange={(e) => setFirstName(e.target.value)}
        />
        <input
          className="border p-2 w-full mb-4"
          placeholder="Prezime"
          value={lastName}
          onChange={(e) => setLastName(e.target.value)}
        />
        <button className="bg-black text-white w-full py-2 rounded">
          Register
        </button>
      </form>
    </div>
  );
}
