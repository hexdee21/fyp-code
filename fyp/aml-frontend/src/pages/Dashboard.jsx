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
        console.log("Loaded flagged transactions:", res.data); // Debug
        setFlagged(res.data.flagged_transactions || []);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);


  // ----- Graph Logic -----
  const generateGraph = useCallback((tx) => {
    if (!tx) return { nodes: [], links: [] };


    // Extract transaction data
    const txData = tx.tx || tx;
    console.log("Generating graph for:", txData); // Debug


    // Rule 35 — coordinated chain
    if (txData.linked_chain_members && txData.linked_chain_common_receiver) {
      const members = txData.linked_chain_members;
      const receiver = txData.linked_chain_common_receiver;
      const origin = members.find((x) => x !== receiver);


      const nodes = members.map((id) => ({
        id,
        color: id === receiver ? "red" : id === origin ? "green" : "blue",
      }));


      const links = [];
      members
        .filter((m) => m !== receiver && m !== origin)
        .forEach((m) => {
          links.push({ source: origin, target: m });
          links.push({ source: m, target: receiver });
        });


      return { nodes, links };
    }


    // ✅ Use full path for layering (Rule 3) or simple path
    let path = txData.path;
   
    // Fallback to simple sender → receiver if no path
    if (!path || path.length === 0) {
      path = [txData.sender, txData.receiver];
    }


    console.log("Using path:", path); // Debug


    // ✅ Create nodes with color coding
    const nodes = path.map((id, idx) => ({
      id,
      color: idx === 0 ? "green" : idx === path.length - 1 ? "red" : "blue"
      // green = origin, red = final destination, blue = intermediaries
    }));


    // Create links between consecutive nodes
    const links = path.slice(0, -1).map((id, i) => ({
      source: path[i],
      target: path[i + 1],
    }));


    console.log("Generated graph:", { nodes, links }); // Debug


    return { nodes, links };
  }, []);


  const openGraph = (tx) => {
    console.log("Opening graph for:", tx); // Debug
    setSelectedTx(tx);
    setGraphData(generateGraph(tx));
  };


  return (
    <div className="min-h-screen bg-gray-100">
      <Navbar />
      <div className="p-6">
        <h1 className="text-3xl font-bold text-red-600 mb-6">🚨 Flagged Transactions</h1>


        {loading ? (
          <p>Loading...</p>
        ) : flagged.length === 0 ? (
          <p>No suspicious activity.</p>
        ) : (
          <table className="w-full bg-white shadow rounded">
            <thead className="bg-gray-200">
              <tr>
                <th className="p-3 text-left">Sender</th>
                <th className="p-3 text-left">Receiver</th>
                <th className="p-3 text-left">Amount</th>
                <th className="p-3 text-left">Path Length</th>
                <th className="p-3 text-left">Rules</th>
                <th className="p-3 text-left">Graph</th>
              </tr>
            </thead>
            <tbody>
              {flagged.map((tx, i) => {
                const txData = tx.tx || tx;
                const path = txData.path || [txData.sender, txData.receiver];
               
                return (
                  <tr key={i} className="border-t hover:bg-gray-50">
                    <td className="p-3 font-mono text-sm">{txData.sender}</td>
                    <td className="p-3 font-mono text-sm">{txData.receiver}</td>
                    <td className="p-3">${txData.amount?.toLocaleString()}</td>
                    <td className="p-3">
                      <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs font-semibold">
                        {path.length} accounts
                      </span>
                    </td>
                    <td className="p-3 text-xs">
                      {(tx.matched_rules || tx.rules_triggered || []).map((rule, idx) => (
                        <span key={idx} className="bg-red-100 text-red-800 px-2 py-1 rounded mr-1 inline-block mb-1">
                          {rule}
                        </span>
                      ))}
                    </td>
                    <td className="p-3">
                      <button
                        onClick={() => openGraph(tx)}
                        className="bg-blue-600 text-white px-3 py-1 rounded text-xs hover:bg-blue-700"
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
        <GraphModal tx={selectedTx} graphData={graphData} onClose={() => setSelectedTx(null)} />
      )}
    </div>
  );
}