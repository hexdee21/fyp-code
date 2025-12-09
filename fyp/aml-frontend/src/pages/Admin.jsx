import React from "react";
import Navbar from "../components/Navbar";
import DepositPanel from "../components/DepositPanel";


export default function Admin() {
  return (
    <div className="min-h-screen bg-gray-100 text-gray-900">
      <Navbar />


      <div className="p-6">
        <h1 className="text-3xl font-bold mb-6 text-green-700">
          🛠 Admin Panel
        </h1>


        <div className="bg-white p-6 rounded shadow">
          <h2 className="text-xl font-semibold mb-4">💰 Deposit Money</h2>
          <DepositPanel />
        </div>
      </div>
    </div>
  );
}
