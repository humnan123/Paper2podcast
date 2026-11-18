import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

export default function MyPapers() {
  const [papers, setPapers] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/papers/mine")
      .then(setPapers)
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div style={{ padding: 16 }}>
      <h2>My submissions</h2>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {papers.length === 0 && !error && (
        <p>You have not submitted any papers yet. <Link to="/conferences">Browse conferences</Link></p>
      )}

      {papers.length > 0 && (
        <table border="1" cellPadding="8" style={{ borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th>Title</th>
              <th>Conference</th>
              <th>Keywords</th>
              <th>Status</th>
              <th>Submitted</th>
            </tr>
          </thead>
          <tbody>
            {papers.map((p) => (
              <tr key={p.id}>
                <td>{p.title}</td>
                <td>{p.conference_name}</td>
                <td>{p.keywords}</td>
                <td>{p.status}</td>
                <td>{new Date(p.submitted_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
