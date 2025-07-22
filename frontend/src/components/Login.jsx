import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./css/Login.css";

function Login({ setAuthenticated }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleLogin = async () => {
    console.log("[DEBUG] Attempting login");
    try {
      const res = await fetch("http://localhost:5000/api/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        credentials: "include",
        body: JSON.stringify({ username, password })
      });

      console.log("[DEBUG] Response status:", res.status);

      if (res.ok) {
        console.log("[DEBUG] Login success");
        setAuthenticated(true);
        navigate("/file_upload");  //  Redirect after login success
      } else {
        const data = await res.json();
        console.log("[DEBUG] Login failed:", data.error);
        alert("Invalid credentials");
      }
    } catch (error) {
      console.error("[DEBUG] Login error:", error);
    }
  };

  return (
    <div className="login-container">
      <h2>Login</h2>
      <input value={username} onChange={e => setUsername(e.target.value)} placeholder="Username" />
      <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" />
      <button onClick={handleLogin}>Login</button>
    </div>
  );
}

export default Login;
