import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

export default function UserPortal() {
  const [receiver, setReceiver] = useState("");
  const [amount, setAmount] = useState("");
  const [category, setCategory] = useState("General");
  const [method, setMethod] = useState("Wire");
  const [msg, setMsg] = useState("");
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("wallet_id");
    localStorage.removeItem("email");
    localStorage.removeItem("userRole");
    navigate("/login", { replace: true });
  };

  const handleSend = async (e) => {
    e.preventDefault();
    setMsg("");
    const token = localStorage.getItem("token");
    const wallet_id = localStorage.getItem("wallet_id");
    const email = localStorage.getItem("email");

    try {
      const res = await axios.post(
        "http://localhost:5000/add_tx",
        { receiver, amount: parseFloat(amount), merchant_category: category, payment_method: method },
        { headers: { Authorization: `Bearer ${token}`, "X-Wallet-ID": wallet_id, "X-User-Email": email } }
      );
      setMsg(`Transaction sent: ${res.data.status}`);
    } catch (err) {
      setMsg("Error sending transaction");
    }
  };

  return (
    <div className="min-h-screen flex justify-center items-center bg-[#0f0f1f] text-neon relative">
      <button onClick={handleLogout} className="absolute top-4 right-4 bg-red-600 hover:brightness-125 text-[#0f0f1f] px-4 py-2 rounded">
        Logout
      </button>
      <div className="bg-[#111128] p-8 rounded shadow w-[420px]">
        <h1 className="text-2xl font-bold text-center mb-4 text-[#00ffff]">💸 Send Transaction</h1>
        {msg && <p className="text-center text-sm mb-3 text-[#00ff99]">{msg}</p>}
        <form onSubmit={handleSend} className="space-y-4">
          <input type="text" className="w-full border border-[#00ffff] p-2 rounded bg-[#ffffff] text-neon" placeholder="Receiver Wallet" value={receiver} onChange={(e) => setReceiver(e.target.value)} required />
          <input type="number" className="w-full border border-[#00ffff] p-2 rounded bg-[#ffffff] text-neon" placeholder="Amount" value={amount} onChange={(e) => setAmount(e.target.value)} required />
          <select className="w-full border border-[#00ffff] p-2 rounded bg-[#ffffff] text-neon" value={category} onChange={(e) => setCategory(e.target.value)}>
            <option>General</option>
            <option>Food</option>
            <option>Shopping</option>
            <option>Healthcare</option>
            <option>Travel</option>
            <option>Transfer</option>
          </select>
          <select className="w-full border border-[#00ffff] p-2 rounded bg-[#ffffff] text-neon" value={method} onChange={(e) => setMethod(e.target.value)}>
            <option>Wire</option>
            <option>Card</option>
            <option>Mobile</option>
            <option>Crypto</option>
            <option>Transfer</option>
          </select>
          <button type="submit" className="w-full bg-[#00ffff] hover:brightness-125 text-[#0f0f1f] py-2 rounded">Send Transaction</button>
        </form>
      </div>
    </div>
  );
}
