import { useEffect, useState } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
} from "react-router-dom";

import Navbar from "./components/Navbar";
import Protected from "./components/Protected";

import { api } from "./api";

import Register from "./pages/Register";
import VerifyOTP from "./pages/VerifyOTP";
import Login from "./pages/Login";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import AdminConferences from "./pages/AdminConferences";


const Page = ({ title }) => (
  <h2 style={{ padding: 16 }}>
    {title}
  </h2>
);


function Home() {

  const [status, setStatus] = useState(
    "checking..."
  );


  useEffect(() => {

    api("/health")
      .then((data) => {
        setStatus(data.status);
      })
      .catch((error) => {
        setStatus(
          "error: " + error.message
        );
      });

  }, []);


  return (
    <div style={{ padding: 16 }}>
      <h2>
        Hello world. Backend status: {status}
      </h2>
    </div>
  );

}



export default function App() {

return (

<BrowserRouter>

<Navbar />

<Routes>


{/* Home */}

<Route
path="/"
element={<Home />}
/>



{/* Authentication */}

<Route
path="/register"
element={<Register />}
/>


<Route
path="/verify-otp"
element={<VerifyOTP />}
/>


<Route
path="/login"
element={<Login />}
/>


<Route
path="/forgot-password"
element={<ForgotPassword />}
/>


<Route
path="/reset-password"
element={<ResetPassword />}
/>



{/* Author protected pages */}

<Route
path="/submit"
element={
<Protected allowedRoles={["author"]}>
<Page title="Submit paper" />
</Protected>
}
/>


<Route
path="/my-papers"
element={
<Protected allowedRoles={["author"]}>
<Page title="My submissions" />
</Protected>
}
/>



{/* Reviewer protected page */}

<Route
path="/assignments"
element={
<Protected allowedRoles={["reviewer"]}>
<Page title="My assignments" />
</Protected>
}
/>



{/* Chairperson page */}

<Route
path="/chair/papers"
element={
<Protected allowedRoles={["chairperson"]}>
<Page title="Chairperson: papers" />
</Protected>
}
/>



{/* Admin page (Part 3) */}

<Route
path="/admin/conferences"
element={
<Protected allowedRoles={["admin"]}>
<AdminConferences />
</Protected>
}
/>



{/* Public conference browsing */}

<Route
path="/conferences"
element={
<Page title="Browse conferences" />
}
/>



</Routes>


</BrowserRouter>

);

}