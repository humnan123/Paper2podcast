import { Link } from "react-router-dom";

export default function Navbar() {

  const role = localStorage.getItem("role") || "guest";


  return (
    <nav style={{
      padding: "15px",
      borderBottom: "1px solid #ddd"
    }}>

      <Link to="/">
        Paper CMS
      </Link>

      {" | "}

      <Link to="/login">
        Login
      </Link>

      {" | "}

      <Link to="/register">
        Register
      </Link>

      {" | "}

      <Link to="/verify-otp">
        Verify OTP
      </Link>


      <span style={{
        marginLeft: "20px"
      }}>
        Role: {role}
      </span>

    </nav>
  );
}