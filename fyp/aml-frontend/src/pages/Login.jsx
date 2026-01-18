import React, { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";


export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();


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
      const res = await axios.post("http://localhost:5005/login", { email, password });
      if (res.data.success) {
        localStorage.setItem("token", res.data.token || "");
        localStorage.setItem("email", email);
        localStorage.setItem("userRole", res.data.role || "user");
        if (res.data.wallet) localStorage.setItem("wallet_id", res.data.wallet);


        if (res.data.role === "admin") navigate("/dashboard", { replace: true });
        else if (res.data.role === "auditor") navigate("/audit", { replace: true });
        else navigate("/portal", { replace: true });
      } else setError(res.data.message || "Invalid credentials");
    } catch (err) {
      setError(err.response?.data?.message || "Server error. Try again.");
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="auth-container h-screen bg-[#0f0f1f] text-neon flex items-center justify-center">
      <div className="auth-box bg-[#111128] p-8 rounded-lg shadow-lg w-96">
        <h1 className="text-2xl font-bold text-center mb-6 text-[#00ffff]">🔐 Login</h1>
        {error && <div className="bg-red-600 text-black p-2 mb-3 rounded text-sm text-center">{error}</div>}
        <form onSubmit={handleLogin} className="space-y-4">
          <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full border border-[#00ffff] p-2 rounded bg-[#ffffff] text-neon" required />
          <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full border border-[#00ffff] p-2 rounded bg-[#ffffff] text-neon" required />
          <button type="submit" disabled={loading} className={`w-full py-2 rounded text-[#0f0f1f] ${loading ? "bg-gray-700" : "bg-[#00ffff] hover:brightness-125"}`}>
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-[#00ffff]">
          Don't have an account?{" "}
          <Link to="/register" className="text-[#00ff99] hover:underline">Register</Link>
        </p>
      </div>
    </div>
  );
}
