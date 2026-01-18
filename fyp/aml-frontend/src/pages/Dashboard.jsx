import React, { useEffect, useState, useCallback } from "react";
import Navbar from "../components/Navbar";
import axios from "axios";
import GraphModal from "../components/GraphModal";


export default function Dashboard() {
  const [flagged, setFlagged] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTx, setSelectedTx] = useState(null);
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const AUDITOR_API = "http://172.25.136.156:5004";


  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const res = await axios.get(`${AUDITOR_API}/view_logs`);
        setFlagged(res.data.flagged_transactions || []);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);


  const generateGraph = useCallback((tx) => {
    if (!tx) return { nodes: [], links: [] };
    const txData = tx.tx || tx;
    let path = txData.path || [txData.sender, txData.receiver];


    const nodes = path.map((id, idx) => ({
      id,
      color: idx === 0 ? "green" : idx === path.length - 1 ? "red" : "blue",
    }));


    const links = path.slice(0, -1).map((id, i) => ({
      source: path[i],
      target: path[i + 1],
    }));


    return { nodes, links };
  }, []);


  const openGraph = (tx) => {
    setSelectedTx(tx);
    setGraphData(generateGraph(tx));
  };


  return (
    <div className="min-h-screen bg-[#0f0f1f] text-neon">


      {/* Full width navbar */}
      <div className="mb-6">
        <Navbar />
      </div>


      {/* Page content */}
      <div className="px-6">
        <h1 className="text-3xl font-bold mb-6 text-[#00ffff]">🚨 Flagged Transactions</h1>


        {loading ? (
          <p className="text-gray-300">Loading...</p>
        ) : flagged.length === 0 ? (
          <p className="text-gray-300">No suspicious activity.</p>
        ) : (
          <table className="w-full bg-[#111128] shadow-[0_0_15px_#00ffff22] rounded overflow-hidden">
            <thead className="bg-[#1a1a2e] text-[#00ffff] border-b border-[#00ffff33]">
              <tr>
                <th className="p-3 text-left">Sender</th>
                <th className="p-3 text-left">Receiver</th>
                <th className="p-3 text-left">Amount</th>
                <th className="p-3 text-left">Path Length</th>
                <th className="p-3 text-left">Rules</th>
                <th className="p-3 text-center">Graph</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#00ffff22]">
              {flagged.map((tx, i) => {
                const txData = tx.tx || tx;
                const path = txData.path || [txData.sender, txData.receiver];


                return (
                  // FIX 1: Added 'text-gray-300' here to make text visible
                  <tr key={i} className="hover:bg-[#111133] transition-colors text-gray-300">
                    <td className="p-3 font-medium text-white">{txData.sender}</td>
                    <td className="p-3 font-medium text-white">{txData.receiver}</td>
                    
                    {/* FIX 2: Formatted Amount with $ and commas */}
                    <td className="p-3 text-[#00ffff]">
                      ${Number(txData.amount).toLocaleString()}
                    </td>


                    {/* FIX 3: Restored the Blue Badge look for Path Length */}
                    <td className="p-3">
                      <span className="bg-blue-900 text-blue-200 px-2 py-1 rounded text-xs border border-blue-500">
                        {path.length} accounts
                      </span>
                    </td>


                    <td className="p-3 text-xs">
                      {(tx.matched_rules || tx.rules_triggered || []).map((rule, idx) => (
                        <span
                          key={idx}
                          className="bg-red-900/50 text-red-200 border border-red-500/50 px-2 py-1 rounded mr-1 inline-block mb-1"
                        >
                          {rule}
                        </span>
                      ))}
                    </td>
                    <td className="p-3 text-center">
                      <button
                        onClick={() => openGraph(tx)}
                        className="bg-[#00ffff] text-[#111128] font-bold px-3 py-1 rounded text-xs hover:bg-white hover:shadow-[0_0_10px_#00ffff] transition-all"
                      >
                        View Graph
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>


      {selectedTx && (
        <GraphModal
          tx={selectedTx}
          graphData={graphData}
          onClose={() => setSelectedTx(null)}
        />
      )}
    </div>
  );
}


