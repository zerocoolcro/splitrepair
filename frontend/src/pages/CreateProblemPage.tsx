import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createProblem } from "@/services/problems.service";
import { toast } from "sonner";

export default function CreateProblemPage() {
  const navigate = useNavigate();

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [address, setAddress] = useState("");
  const [latitude, setLatitude] = useState<number | "">("");
  const [longitude, setLongitude] = useState<number | "">("");
  const [loading, setLoading] = useState(false);

  const handleGetLocation = () => {
    if (!navigator.geolocation) {
        alert("Geolocation nije podržan.");
        return;
    }

    navigator.geolocation.getCurrentPosition(
        (position) => {
            setLatitude(position.coords.latitude);
            setLongitude(position.coords.longitude);
        },
        (error) => {
            alert("Ne mogu dohvatiti lokaciju.");
            console.error(error);
        }
    );
};
  
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    if (!file) {
        alert("Slika je obavezna.");
        setLoading(false);
        return;
    }

    try {
      const formData = new FormData();
      formData.append("title", title);
      formData.append("description", description);

      if (file) {
        formData.append("file", file);
      }

      if (address) {
        formData.append("address", address);
      }

      if (latitude !== "") {
        formData.append("latitude", String(latitude));
      }

      if (longitude !== "") {
        formData.append("longitude", String(longitude));
      }

      await createProblem(formData);

      toast.success("Problem uspješno kreiran!");

      navigate("/dashboard");
    } catch (error) {
      console.error(error);
      toast.error("Došlo je do greške!");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">➕ Prijavi problem</h1>

      <form onSubmit={handleSubmit} className="space-y-4">

        <div>
          <label className="block mb-1 font-medium">Naslov *</label>
          <input
            type="text"
            required
            className="w-full border p-2 rounded"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>

        <div>
          <label className="block mb-1 font-medium">Opis *</label>
          <textarea
            required
            rows={4}
            className="w-full border p-2 rounded"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>

        <div>
          <label className="block mb-1 font-medium">Adresa</label>
          <input
            type="text"
            className="w-full border p-2 rounded"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">

          <div>
            <label className="block mb-1 font-medium">Latitude</label>
            <input
              type="number"
              step="any"
              className="w-full border p-2 rounded"
              value={latitude}
              onChange={(e) =>
                setLatitude(e.target.value === "" ? "" : Number(e.target.value))
              }
            />
          </div>

          <div>
            <label className="block mb-1 font-medium">Longitude</label>
            <input
              type="number"
              step="any"
              className="w-full border p-2 rounded"
              value={longitude}
              onChange={(e) =>
                setLongitude(e.target.value === "" ? "" : Number(e.target.value))
              }
            />
          </div>
          <div>
                <button
                    type="button"
                    onClick={handleGetLocation}
                    className="bg-green-600 text-white px-4 py-2 rounded"
                >
                    📍 Uzmi moju lokaciju
                </button>
            </div>
        </div>

        <div>
          <label className="block mb-1 font-medium">Slika</label>
          <input
            type="file"
            required
            className="w-full"
            onChange={(e) =>
              setFile(e.target.files ? e.target.files[0] : null)
            }
          />
        </div>

        <div className="flex gap-4">
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 text-white px-4 py-2 rounded"
          >
            {loading ? "Šaljem..." : "Prijavi"}
          </button>

          <button
            type="button"
            onClick={() => navigate("/dashboard")}
            className="bg-gray-200 px-4 py-2 rounded"
          >
            Odustani
          </button>
        </div>
      </form>
    </div>
  );
}
