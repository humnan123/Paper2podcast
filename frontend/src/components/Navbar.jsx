import { Link } from "react-router-dom";

const LINKS = {
  guest: [["/login", "Login"], ["/register", "Register"]],
  author: [["/conferences", "Conferences"], ["/submit", "Submit paper"], ["/my-papers", "My submissions"]],
  reviewer: [["/assignments", "My assignments"]],
  chairperson: [["/chair/papers", "Papers"]],
  admin: [["/admin/conferences", "Conferences"]],
};

export default function Navbar() {
  const role = localStorage.getItem("role") || "guest";
  const links = LINKS[role] || LINKS.guest;
  return (
    <nav style={{ display: "flex", gap: 16, padding: 12, borderBottom: "1px solid #ccc" }}>
      <strong>Paper CMS</strong>
      {links.map(([to, label]) => (
        <Link key={to} to={to}>{label}</Link>
      ))}
      <span style={{ marginLeft: "auto" }}>Role: {role}</span>
    </nav>
  );
}