import { useEffect, useState, useRef } from "react";
import axios from "axios";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { useLocation } from "react-router-dom";
import MarkerClusterGroup from "react-leaflet-cluster";

interface Problem {
  id: number;
  title: string;
  description: string;
  status: {
    name: string;
  };
  location?: {
    latitude?: number;
    longitude?: number;
    address?: string;
  };
}

interface ApiResponse {
  items: Problem[];
  page: number;
  total_pages: number;
  next_page: number | null;
  prev_page: number | null;
}

const redIcon = new L.Icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

const yellowIcon = new L.Icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-yellow.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

const greenIcon = new L.Icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

const getStatusIcon = (status: string) => {
  if (status === "open") return redIcon;
  if (status === "pending") return yellowIcon;
  if (status === "resolved") return greenIcon;
  return redIcon;
};

function ProblemMarker({
  problem,
  selectedLat,
  selectedLng,
  setActiveId,
}: {
  problem: Problem;
  selectedLat?: number;
  selectedLng?: number;
  setActiveId: (id: number) => void;
}) {
  const markerRef = useRef<L.Marker>(null);

  useEffect(() => {
    if (
      selectedLat === problem.location?.latitude &&
      selectedLng === problem.location?.longitude
    ) {
      markerRef.current?.openPopup();
    }
  }, [selectedLat, selectedLng, problem]);

  if (
    problem.location?.latitude === undefined ||
    problem.location?.longitude === undefined
  ) {
    return null;
  }

  return (
    <Marker
      ref={markerRef}
      position={[problem.location.latitude, problem.location.longitude]}
      icon={getStatusIcon(problem.status.name)}
      eventHandlers={{
        click: () => setActiveId(problem.id),
      }}
    >
      <Popup>
        <strong>{problem.title}</strong>
        <br />
        {problem.description}
        <br />
        Status: {problem.status?.name}
      </Popup>
    </Marker>
  );
}

export default function MapPage() {
  const [problems, setProblems] = useState<Problem[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [nextPage, setNextPage] = useState<number | null>(null);
  const [prevPage, setPrevPage] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [activeId, setActiveId] = useState<number | null>(null);
  const location = useLocation();
  const selectedLat = location.state?.lat;
  const selectedLng = location.state?.lng;

  useEffect(() => {
    if (selectedLat !== undefined && selectedLng !== undefined) {
      const found = problems.find(
        (p) =>
          p.location?.latitude === selectedLat &&
          p.location?.longitude === selectedLng
      );

      if (found) {
        setActiveId(found.id);
      }
    }
  }, [selectedLat, selectedLng, problems]);

  useEffect(() => {
    fetchProblems();
  }, [page, search, status]);

  const fetchProblems = async () => {
    setLoading(true);

    try {
      const response = await axios.get<ApiResponse>(
        `http://127.0.0.1:8000/problems?page=${page}&limit=5&search=${search}&status=${status}`
      );

      setProblems(response.data.items);
      setTotalPages(response.data.total_pages);
      setNextPage(response.data.next_page);
      setPrevPage(response.data.prev_page);
    } catch (error) {
      console.error("Greška pri dohvaćanju problema:", error);
    } finally {
      setLoading(false);
    }
  };

  function ChangeView({ lat, lng }: { lat: number; lng: number }) {
    const map = useMap();

    useEffect(() => {
      if (lat !== undefined && lng !== undefined) {
        map.flyTo([lat, lng], 16);
      }
    }, [lat, lng, map]);

    return null;
  }

  return (
    <div className="min-h-screen p-6 bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* CENTRALNI CONTAINER */}
      <div className="max-w-xl mx-auto">

        {/* FILTERS */}
        <div className="mb-6">
          <div className="flex gap-4">
            <input
              type="text"
              placeholder="Pretraži..."
              value={search}
              onChange={(e) => {
                setPage(1);
                setSearch(e.target.value);
              }}
              className="w-full px-4 py-2 rounded-xl border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white/80 backdrop-blur"
            />

            <select
              value={status}
              onChange={(e) => {
                setPage(1);
                setStatus(e.target.value);
              }}
              className="w-40 px-4 py-2 rounded-xl border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white/80 backdrop-blur"
            >
              <option value="">Svi statusi</option>
              <option value="open">Open</option>
              <option value="pending">Pending</option>
              <option value="resolved">Resolved</option>
            </select>
          </div>
        </div>

        {/* MAPA */}
        <div className="h-[400px] md:h-[500px] w-full mb-8 rounded-2xl overflow-hidden shadow-2xl border border-white/40">
          <MapContainer
            center={[43.5081, 16.4402]} // Split
            zoom={13}
            className="h-full w-full"
          >

            {selectedLat !== undefined && selectedLng !== undefined && (
              <ChangeView lat={selectedLat} lng={selectedLng} />
            )}

            <TileLayer
              attribution="&copy; OpenStreetMap contributors"
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            <MarkerClusterGroup>
              {problems.map((problem) =>
                problem.location?.latitude && problem.location?.longitude ? (
                  <Marker
                    key={problem.id}
                    position={[problem.location.latitude, problem.location.longitude]}
                    icon={getStatusIcon(problem.status.name)}
                    eventHandlers={{
                      click: () => setActiveId(problem.id),
                    }}
                  >
                    <Popup>
                      <strong>{problem.title}</strong>
                      <br />
                      {problem.description}
                    </Popup>
                  </Marker>
                ) : null
              )}
            </MarkerClusterGroup>

          </MapContainer>
        </div>

        {/* LISTA PROBLEMA */}
        <div className="space-y-4">
          {loading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-24 rounded-2xl bg-gray-200 animate-pulse"
                />
              ))}
            </div>
          ) : (
            problems.map((problem) => (
              <div
                key={problem.id}
                className={`fade-in p-5 rounded-2xl shadow-xl backdrop-blur-md bg-white/70 border border-white/40 transition hover:scale-[1.03] hover:-translate-y-1 hover:shadow-2xl duration-200 ${
                  activeId === problem.id ? "ring-2 ring-blue-500 bg-blue-50/80" : ""
                }`}
              >
                <h2 className="text-lg font-semibold">{problem.title}</h2>
                <p className="text-gray-600">{problem.description}</p>
                <span className="text-sm font-medium">
                  Status: {problem.status.name}
                </span>
              </div>
            ))
          )}
        </div>

        {/* PAGINACIJA */}
        <div className="flex justify-between items-center mt-6">
          <button
            disabled={!prevPage}
            onClick={() => prevPage && setPage(prevPage)}
            className="px-4 py-2 rounded-xl bg-blue-600 text-white hover:bg-blue-700 hover:scale-105 transition duration-200 shadow-md disabled:opacity-50"
          >
            ← Prethodna
          </button>

          <span>
            Stranica {page} / {totalPages}
          </span>

          <button
            disabled={!nextPage}
            onClick={() => nextPage && setPage(nextPage)}
            className="px-4 py-2 bg-gray-200 rounded disabled:opacity-50"
          >
            Sljedeća →
          </button>
        </div>

      </div>
    </div>
  );
}

