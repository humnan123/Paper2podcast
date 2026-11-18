import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

export default function BrowseConferences() {
  const [conferences, setConferences] = useState([]);
  const [error, setError] = useState("");
  const role = localStorage.getItem("role");

  useEffect(() => {
    api("/conferences")
      .then((all) => setConferences(all.filter((c) => c.status === "open")))
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div style={{ padding: 16 }}>
      <h2>Open conferences</h2>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {conferences.length === 0 && !error && <p>No open conferences right now.</p>}

      {conferences.map((c) => (
        <div key={c.id} style={{ border: "1px solid #ddd", padding: 12, marginBottom: 12 }}>
          <h3>{c.name}</h3>
          {c.description && <p>{c.description}</p>}
          <p>
            Conference: {c.start_date} to {c.end_date}
            <br />
            Submission deadline: {new Date(c.submission_deadline).toLocaleDateString()}
          </p>
          {role === "author" && (
            <Link to={`/submit?conference=${c.id}`}>Submit a paper</Link>
          )}
        </div>
      ))}
    </div>
  );
}
