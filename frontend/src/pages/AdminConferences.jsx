import { useEffect, useState } from "react";
import { api } from "../api";

const empty = {
  name: "",
  description: "",
  start_date: "",
  end_date: "",
  submission_deadline: "",
  chairperson_email: "",
};

export default function AdminConferences() {
  const [form, setForm] = useState(empty);
  const [conferences, setConferences] = useState([]);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const load = () =>
    api("/conferences")
      .then(setConferences)
      .catch((err) => setError(err.message));

  useEffect(() => {
    load();
  }, []);

  const onChange = (e) =>
    setForm({ ...form, [e.target.name]: e.target.value });

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    try {
      await api("/conferences", {
        method: "POST",
        body: form,
      });
      setSuccess("Conference created");
      setForm(empty);
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div>
      <h2>Create conference</h2>
      <form onSubmit={onSubmit}>
        <input name="name" placeholder="Name" value={form.name} onChange={onChange} required />
        <textarea name="description" placeholder="Description" value={form.description} onChange={onChange} />
        <label>
          Start <input type="date" name="start_date" value={form.start_date} onChange={onChange} required />
        </label>
        <label>
          End <input type="date" name="end_date" value={form.end_date} onChange={onChange} required />
        </label>
        <label>
          Submission deadline{" "}
          <input type="date" name="submission_deadline" value={form.submission_deadline} onChange={onChange} required />
        </label>
        <input name="chairperson_email" placeholder="Chairperson email" value={form.chairperson_email} onChange={onChange} required />
        <button type="submit">Create</button>
      </form>

      {error && <p style={{ color: "red" }}>{error}</p>}
      {success && <p style={{ color: "green" }}>{success}</p>}

      <h2>Conferences</h2>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Start</th>
            <th>Deadline</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {conferences.map((c) => (
            <tr key={c.id}>
              <td>{c.name}</td>
              <td>{c.start_date}</td>
              <td>{c.submission_deadline}</td>
              <td>{c.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}