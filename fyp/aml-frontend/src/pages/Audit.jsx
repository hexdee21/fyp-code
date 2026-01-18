import React, { useEffect, useState, useCallback } from "react";
import Navbar from "../components/Navbar";
import axios from "axios";
import GraphModal from "../components/GraphModal";


export default function Audit() {
  const [txs, setTxs] = useState([]);
  const [selectedTx, setSelectedTx] = useState(null);
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const MINER_API = "http://172.25.136.156:5000";


  useEffect(() => {
    async function load() {
      try {
        const res = await axios.get(`${MINER_API}/chain`);
        const blocks = res.data || [];


        const all = blocks.flatMap((b) =>
          (b.transactions || []).map((t) => ({
            ...t,
            blockIndex: b.index,
          }))
        );


        setTxs(all);
      } catch (err) {
        console.error("Failed to fetch blockchain data", err);
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
        <h1 className="text-3xl font-bold mb-6 text-[#00ffff]">🧾 Audit Logs</h1>


        <table className="w-full bg-[#111128] shadow-[0_0_15px_#00ffff22] rounded overflow-hidden">
          {/* FIX 1: Styled the header with neon text and border */}
          <thead className="bg-[#1a1a2e] text-[#00ffff] border-b border-[#00ffff33]">
            <tr>
              <th className="p-3 text-left">Sender</th>
              <th className="p-3 text-left">Receiver</th>
              <th className="p-3 text-left">Amount</th>
              <th className="p-3 text-left">Block</th>
              <th className="p-3 text-center">Graph</th>
            </tr>
          </thead>
          
          {/* FIX 2: Added light gray text color to body and neon dividers */}
          <tbody className="divide-y divide-[#00ffff22]">
            {txs.map((tx, i) => (
              <tr key={i} className="hover:bg-[#111133] transition-colors text-gray-300">
                <td className="p-3 font-medium text-white">{tx.sender}</td>
                <td className="p-3 font-medium text-white">{tx.receiver}</td>
                
                {/* FIX 3: Formatted Amount with $ and commas */}
                <td className="p-3 text-[#00ffff]">
                  ${Number(tx.amount).toLocaleString()}
                </td>
                
                <td className="p-3 text-gray-400">Block #{tx.blockIndex}</td>
                
                <td className="p-3 text-center">
                  <button
                    onClick={() => openGraph(tx)}
                    className="bg-[#00ffff] text-[#111128] font-bold px-3 py-1 rounded text-xs hover:bg-white hover:shadow-[0_0_10px_#00ffff] transition-all"
                  >
                    View Graph
                  </button>
                </td>
              </tr>
            ))}
            {txs.length === 0 && (
              <tr>
                <td colSpan="5" className="p-6 text-center text-gray-500">
                  No transactions found on the blockchain yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
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


