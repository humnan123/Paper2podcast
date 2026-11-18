import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api";

export default function SubmitPaper() {
  const [params] = useSearchParams();
  const navigate = useNavigate();

  const [conferences, setConferences] = useState([]);
  const [conferenceId, setConferenceId] = useState(params.get("conference") || "");
  const [title, setTitle] = useState("");
  const [abstract, setAbstract] = useState("");
  const [keywords, setKeywords] = useState("");
  const [file, setFile] = useState(null);
  const [terms, setTerms] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api("/conferences")
      .then((all) => setConferences(all.filter((c) => c.status === "open")))
      .catch((err) => setError(err.message));
  }, []);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!conferenceId) return setError("Please choose a conference");
    if (!file) return setError("Please choose a PDF file");
    if (!terms) return setError("You must accept the terms");

    const form = new FormData();
    form.append("conference_id", conferenceId);
    form.append("title", title);
    form.append("abstract", abstract);
    form.append("keywords", keywords);
    form.append("terms_accepted", terms ? "true" : "false");
    form.append("file", file);

    setBusy(true);
    try {
      await api("/papers", { method: "POST", body: form });
      navigate("/my-papers");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ padding: 16, maxWidth: 600 }}>
      <h2>Submit a paper</h2>
      {error && <p style={{ color: "red" }}>{error}</p>}

      <form onSubmit={onSubmit} style={{ display: "grid", gap: 10 }}>
        <select value={conferenceId} onChange={(e) => setConferenceId(e.target.value)} required>
          <option value="">Choose a conference</option>
          {conferences.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>

        <input placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} required />
        <textarea placeholder="Abstract" rows={6} value={abstract} onChange={(e) => setAbstract(e.target.value)} required />
        <input placeholder="Keywords (comma separated)" value={keywords} onChange={(e) => setKeywords(e.target.value)} />

        <label>
          PDF file (max 10 MB){" "}
          <input type="file" accept="application/pdf,.pdf" onChange={(e) => setFile(e.target.files[0] || null)} required />
        </label>

        <label>
          <input type="checkbox" checked={terms} onChange={(e) => setTerms(e.target.checked)} />{" "}
          I accept the terms and confirm this is my own work
        </label>

        <button type="submit" disabled={busy}>
          {busy ? "Submitting..." : "Submit paper"}
        </button>
      </form>
    </div>
  );
}
