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
      const res = await axios.get(`${MINER_API}/chain`);
      const blocks = res.data || [];


      const all = blocks.flatMap((b) =>
        (b.transactions || []).map((t) => ({
          ...t,
          blockIndex: b.index,
        }))
      );


      setTxs(all);
    }
    load();
  }, []);


  // ----- Graph Logic -----
  const generateGraph = useCallback((tx) => {
    if (!tx) return { nodes: [], links: [] };


    if (tx.tx) tx = tx.tx;


    if (tx.linked_chain_members && tx.linked_chain_common_receiver) {
      const mem = tx.linked_chain_members;
      const rec = tx.linked_chain_common_receiver;
      const origin = mem.find((x) => x !== rec);


      const nodes = mem.map((id) => ({
        id,
        color: id === rec ? "red" : id === origin ? "green" : "blue",
      }));


      const links = [];
      mem.filter((m) => m !== rec && m !== origin).forEach((m) => {
        links.push({ source: origin, target: m });
        links.push({ source: m, target: rec });
      });


      return { nodes, links };
    }


    let path = tx.path;
    if (!path && tx.sender && tx.receiver) {
      path = [tx.sender, tx.receiver];
    }
    if (!path) return { nodes: [], links: [] };


    const nodes = path.map((id) => ({ id, color: "blue" }));
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
    <div className="min-h-screen bg-gray-100">
      <Navbar />
      <div className="p-6">
        <h1 className="text-3xl font-bold mb-6 text-indigo-600">
          🧾 Audit Logs (All Transactions)
        </h1>


        <table className="w-full bg-white shadow rounded">
          <thead className="bg-gray-200">
            <tr>
              <th className="p-3">Sender</th>
              <th className="p-3">Receiver</th>
              <th className="p-3">Amount</th>
              <th className="p-3">Block</th>
              <th className="p-3">Graph</th>
            </tr>
          </thead>
          <tbody>
            {txs.map((tx, i) => (
              <tr key={i} className="border-t hover:bg-gray-50">
                <td className="p-3">{tx.sender}</td>
                <td className="p-3">{tx.receiver}</td>
                <td className="p-3">{tx.amount}</td>
                <td className="p-3">{tx.blockIndex}</td>
                <td className="p-3">
                  <button
                    onClick={() => openGraph(tx)}
                    className="bg-blue-600 text-white px-3 py-1 rounded text-xs"
                  >
                    View Graph
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>


      {selectedTx && (
        <GraphModal tx={selectedTx} graphData={graphData} onClose={() => setSelectedTx(null)} />
      )}
    </div>
  );
}

