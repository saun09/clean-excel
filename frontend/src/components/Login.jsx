import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./css/Login.css";
import logo from "../assets/AGRLogo.jpeg";

function Login({ setAuthenticated }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleLogin = async () => {
    try {
      const res = await fetch("http://localhost:5000/api/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        credentials: "include",
        body: JSON.stringify({ username, password })
      });

      if (res.ok) {
        setAuthenticated(true);
        navigate("/file_upload");
      } else {
        const data = await res.json();
        alert(data.error || "Invalid credentials");
      }
    } catch (error) {
      console.error("Login error:", error);
      alert("Something went wrong. Please try again.");
    }
  };

  return (
    <div className="login-container">
  <div className="login-card">
    <img src={logo} alt="AGR Logo" className="login-logo" />
    <h1 className="product-title">Xelly</h1>
    <h2 className="login-title">Login to your account</h2>

    <input
      value={username}
      onChange={e => setUsername(e.target.value)}
      placeholder="Username"
      className="login-input"
    />
    <input
      type="password"
      value={password}
      onChange={e => setPassword(e.target.value)}
      placeholder="Password"
      className="login-input"
    />

    <button onClick={handleLogin} className="login-button">Login</button>

    {/* Footer inside login card */}
    <div className="developer-footer">
      <p className="animated-text">Developed by <span>Saundarya</span></p>
      <a
        href="https://www.linkedin.com/in/saundarya-subramaniam"
        target="_blank"
        rel="noopener noreferrer"
        className="linkedin-button"
      >
        LinkedIn
      </a>
    </div>
  </div>
</div>

  );
}

export default Login;
