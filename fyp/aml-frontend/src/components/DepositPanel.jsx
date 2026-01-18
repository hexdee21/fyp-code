import { useState } from "react";
import axios from "axios";

export default function DepositPanel() {
  const [wallet, setWallet] = useState("");
  const [amount, setAmount] = useState("");
  const [msg, setMsg] = useState("");

  const handleDeposit = async (e) => {
    e.preventDefault();
    setMsg("");

    try {
      const token = localStorage.getItem("token");

      const res = await axios.post(
        "http://localhost:5005/admin/deposit",
        { wallet_id: wallet, amount },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );

      setMsg(res.data.message || "Deposit successful!");
      setWallet("");
      setAmount("");
    } catch (err) {
      setMsg("❌ Error: " + (err.response?.data?.message || "Failed"));
    }
  };

  return (
    <div>
      {msg && (
        <p className="p-2 mb-2 text-sm rounded bg-[#ffffff] text-neon border border-[#00ffff]">
          {msg}
        </p>
      )}

      <form onSubmit={handleDeposit} className="flex gap-3">
        <input
          type="text"
          placeholder="Wallet ID"
          value={wallet}
          onChange={(e) => setWallet(e.target.value)}
          className="border p-2 rounded w-40 bg-[#ffffff] text-neon border-[#00ffff]"
          required
        />

        <input
          type="number"
          placeholder="Amount"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          className="border p-2 rounded w-32 bg-[#ffffff] text-neon border-[#00ffff]"
          required
        />

        <button
          type="submit"
          className="bg-green-600 text-black px-4 py-2 rounded hover:brightness-150"
        >
          Deposit
        </button>
      </form>
    </div>
  );
}
