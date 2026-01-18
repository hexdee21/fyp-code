import React from "react";
import Navbar from "../components/Navbar";
import DepositPanel from "../components/DepositPanel";

export default function Admin() {
  return (
    <div className="min-h-screen bg-[#0f0f1f] text-neon">
      <Navbar />
      <div className="p-6">
        <h1 className="text-3xl font-bold mb-6 text-[#00ffff]">🛠 Admin Panel</h1>
        <div className="bg-[#111128] p-6 rounded shadow">
          <h2 className="text-xl font-semibold mb-4 text-[#00ff99]">💰 Deposit Money</h2>
          <DepositPanel />
        </div>
      </div>
    </div>
  );
}
