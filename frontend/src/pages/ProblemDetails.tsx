import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { api } from "@/services/api";
import { useAuth } from "@/hooks/useAuth";
import { voteProblem } from "@/services/votes.service";

interface Problem {
  id: number;
  title: string;
  description: string;
  votes: number;
}

interface Comment {
  id: number;
  content: string;
  author: string;
}

export default function ProblemDetail() {
  const { id } = useParams();
  const { user } = useAuth();

  const [problem, setProblem] = useState<Problem | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [text, setText] = useState("");
  const [votes, setVotes] = useState(0);

  useEffect(() => {
    api.get(`/problems/${id}`).then((res) => {
      setProblem(res.data);
      setVotes(res.data.votes);
    });

    api.get(`/problems/${id}/comments`).then((res) => setComments(res.data));
  }, [id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await api.post(`/problems/${id}/comments`, { content: text });
    setComments((prev) => [...prev, res.data]);
    setText("");
  };

  const handleVote = async (value: 1 | -1) => {
    setVotes((v) => v + value); // optimistic UI

    try {
      await voteProblem(Number(id), value);
    } catch (err) {
      setVotes((v) => v - value); // rollback ako faila
    }
  };

  if (!problem) return <div className="p-6">Loading...</div>;

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold">{problem.title}</h1>
      <p className="mt-2 text-gray-700">{problem.description}</p>

      {/* VOTES */}
      <div className="flex items-center gap-4 mt-4">
        <button
          onClick={() => handleVote(1)}
          className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600"
        >
          👍
        </button>

        <span className="font-semibold text-lg">{votes}</span>

        <button
          onClick={() => handleVote(-1)}
          className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600"
        >
          👎
        </button>
      </div>

      {/* KOMENTARI */}
      <h2 className="mt-6 font-semibold">Komentari</h2>

      <div className="space-y-3 mt-3">
        {comments.map((c) => (
          <div key={c.id} className="bg-gray-100 p-3 rounded">
            <p className="text-sm text-gray-800">{c.content}</p>
            <p className="text-xs text-gray-500">— {c.author}</p>
          </div>
        ))}
      </div>

      {user && (
        <form onSubmit={handleSubmit} className="mt-4">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="w-full border rounded p-2"
            placeholder="Dodaj komentar..."
          />
          <button className="mt-2 bg-blue-500 text-white px-4 py-2 rounded">
            Pošalji
          </button>
        </form>
      )}
    </div>
  );
}
