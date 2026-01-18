import React, { useState } from "react";
import axios from "axios";
import { useNavigate, Link } from "react-router-dom";

export default function Register() {
  const [email, setEmail] = useState("");
  const [passport, setPassport] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    try {
      const res = await axios.post("http://localhost:5005/register", {
        email,
        password,
        passport_number: passport,
        role: "user",
      });
      if (res.data.success) {
        setSuccess("Account created! Redirecting to login...");
        setTimeout(() => navigate("/login"), 1500);
      } else setError(res.data.message || "Registration failed.");
    } catch (err) {
      setError(err.response?.data?.message || "Server error");
    }
  };

  return (
    <div className="h-screen flex items-center justify-center bg-[#0f0f1f] text-neon">
      <div className="bg-[#111128] p-8 rounded-lg shadow-lg w-96">
        <h1 className="text-2xl font-bold text-center mb-6 text-[#00ff99]">📝 Register</h1>
        {error && <p className="bg-red-600 text-black p-2 mb-3 rounded">{error}</p>}
        {success && <p className="bg-green-600 text-black p-2 mb-3 rounded">{success}</p>}
        <form onSubmit={handleRegister} className="space-y-4">
          <input type="email" placeholder="Email" className="w-full border border-[#00ff99] p-2 rounded bg-[#ffffff] text-neon" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <input type="text" placeholder="Passport Number" className="w-full border border-[#00ff99] p-2 rounded bg-[#ffffff] text-neon" value={passport} onChange={(e) => setPassport(e.target.value)} required />
          <input type="password" placeholder="Password" className="w-full border border-[#00ff99] p-2 rounded bg-[#ffffff] text-neon" value={password} onChange={(e) => setPassword(e.target.value)} required />
          <button className="w-full bg-[#00ff99] hover:brightness-125 text-[#0f0f1f] py-2 rounded">Register</button>
        </form>
        <p className="mt-3 text-center text-sm text-[#ffffff]">
          Already have an account?{" "}
          <Link to="/login" className="text-[#00ff99] hover:underline">Login</Link>
        </p>
      </div>
    </div>
  );
}
