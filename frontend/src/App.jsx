import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import { api } from "./api";

const Page = ({ title }) => <h2 style={{ padding: 16 }}>{title}</h2>;

function Home() {
  const [status, setStatus] = useState("checking...");
  useEffect(() => {
    api("/health")
      .then((d) => setStatus(d.status))
      .catch((e) => setStatus("error: " + e.message));
  }, []);
  return <h2 style={{ padding: 16 }}>Hello world. Backend status: {status}</h2>;
}

const ROUTES = [
  ["/login", "Login"],
  ["/register", "Register"],
  ["/verify-otp", "Verify OTP"],
  ["/forgot-password", "Forgot password"],
  ["/reset-password", "Reset password"],
  ["/conferences", "Browse conferences"],
  ["/submit", "Submit paper"],
  ["/my-papers", "My submissions"],
  ["/assignments", "My assignments"],
  ["/chair/papers", "Chairperson: papers"],
  ["/admin/conferences", "Admin: conferences"],
];

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        {ROUTES.map(([path, title]) => (
          <Route key={path} path={path} element={<Page title={title} />} />
        ))}
      </Routes>
    </BrowserRouter>
  );
}