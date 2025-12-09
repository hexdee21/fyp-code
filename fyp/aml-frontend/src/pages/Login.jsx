import React, { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";


export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();


  // 👇 Redirect if already logged in (use token only)
  useEffect(() => {
    const token = localStorage.getItem("token");
    const role = localStorage.getItem("userRole");


    if (token) {
      if (role === "admin") navigate("/dashboard", { replace: true });
      else if (role === "auditor") navigate("/audit", { replace: true });
      else navigate("/portal", { replace: true });
    }
  }, [navigate]);


  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);


    try {
      const API_URL = "http://localhost:5005/login";


      const res = await axios.post(API_URL, { email, password });


      if (res.data.success) {
        // ----------------------------------------------------
        // 🧠 Save login details (NO MORE loggedIn)
        // ----------------------------------------------------
        localStorage.setItem("token", res.data.token || "");
        localStorage.setItem("email", email);
        localStorage.setItem("userRole", res.data.role || "user");


        if (res.data.wallet) {
          localStorage.setItem("wallet_id", res.data.wallet);
        }


        // ----------------------------------------------------
        // 🚀 Redirect based on role
        // ----------------------------------------------------
        if (res.data.role === "admin") {
          navigate("/dashboard", { replace: true });
        } else if (res.data.role === "auditor") {
          navigate("/audit", { replace: true });
        } else {
          navigate("/portal", { replace: true }); // NORMAL USER
        }
      } else {
        setError(res.data.message || "Invalid credentials");
      }
    } catch (err) {
      console.error("Login error:", err);
      setError(err.response?.data?.message || "Server error. Try again.");
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-md w-96">
        <h1 className="text-2xl font-bold text-center mb-6 text-blue-600">
          🔐 Login
        </h1>


        {error && (
          <div className="bg-red-100 text-red-700 p-2 mb-3 rounded text-sm text-center">
            {error}
          </div>
        )}


        <form onSubmit={handleLogin} className="space-y-4">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full border p-2 rounded"
            required
          />


          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full border p-2 rounded"
            required
          />


          <button
            type="submit"
            disabled={loading}
            className={`w-full py-2 rounded text-white ${
              loading ? "bg-gray-400" : "bg-blue-600 hover:bg-blue-700"
            }`}
          >
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>


        <p className="mt-4 text-center text-sm text-gray-600">
          Don't have an account?{" "}
          <Link to="/register" className="text-blue-600 hover:underline">
            Register
          </Link>
        </p>
      </div>
    </div>
  );
}