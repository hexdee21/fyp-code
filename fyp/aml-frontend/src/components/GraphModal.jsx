import React from "react";
import ForceGraph2D from "react-force-graph-2d";


export default function GraphModal({ tx, graphData, onClose }) {
  if (!tx) return null;


  // Extract transaction data (handle both nested and flat structure)
  const txData = tx.tx || tx;
  const path = txData.path || [txData.sender, txData.receiver];


  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 z-50 flex items-center justify-center p-4">
      <div className="relative bg-white rounded-lg shadow-lg w-[95vw] h-[85vh] p-4 overflow-auto">
       
        <button
          className="absolute top-3 right-4 text-2xl font-bold text-gray-700 hover:text-black z-10"
          onClick={onClose}
        >
          ✕
        </button>


        <h2 className="text-xl font-semibold text-center mb-3">
          Transaction Graph
        </h2>


        {/* ✅ FULL PATH DISPLAY */}
        <div className="text-center text-gray-700 mb-3 bg-blue-50 p-3 rounded border border-blue-200">
          <p className="font-semibold text-base mb-1">
            📍 Full Transaction Path ({path.length} accounts)
          </p>
          <p className="text-sm font-mono break-all text-blue-800">
            {path.join(" → ")}
          </p>
        </div>


        {/* Transaction Details */}
        <div className="text-center text-gray-600 mb-4 text-sm">
          <div className="flex justify-center gap-4 flex-wrap">
            <span><b>Origin:</b> {path[0] || txData.sender}</span>
            <span><b>Destination:</b> {path[path.length - 1] || txData.receiver}</span>
            <span><b>Amount:</b> ${txData.amount?.toLocaleString()}</span>
            {txData.total_amount && txData.total_amount !== txData.amount && (
              <span className="text-orange-600">
                <b>Total (all hops):</b> ${txData.total_amount?.toLocaleString()}
              </span>
            )}
          </div>
        </div>


        {/* ✅ LAYERING METRICS (if Rule 3 triggered) */}
        {txData.num_layers > 0 && (
          <div className="text-center text-xs text-gray-600 mb-3 bg-yellow-50 p-2 rounded border border-yellow-200">
            <span className="font-semibold text-red-600">⚠️ Layering Detected:</span>
            {" "}
            <span>Layers: {txData.num_layers}</span> |
            <span> Accounts: {txData.num_accounts_involved}</span> |
            <span> Avg Delay: {txData.avg_delay_between_layers?.toFixed(2)}s</span>
          </div>
        )}


        {/* Force Graph */}
        <div className="border border-gray-300 rounded bg-white">
          <ForceGraph2D
            graphData={graphData}
            width={window.innerWidth * 0.9}
            height={window.innerHeight * 0.55}
            nodeRelSize={8}
            backgroundColor="#ffffff"
            linkDirectionalArrowLength={8}
            linkDirectionalArrowRelPos={1}
            linkColor={() => "#666"}
            linkWidth={2}
            nodeCanvasObject={(node, ctx, scale) => {
              const label = node.id;
              const fontSize = 14 / scale;
              const nodeRadius = 6;
             
              // Draw node circle
              ctx.beginPath();
              ctx.arc(node.x, node.y, nodeRadius, 0, 2 * Math.PI);
              ctx.fillStyle = node.color || "blue";
              ctx.fill();
              ctx.strokeStyle = "#fff";
              ctx.lineWidth = 2;
              ctx.stroke();
             
              // Draw label below node
              ctx.font = `${fontSize}px Sans-Serif`;
              ctx.fillStyle = "black";
              ctx.textAlign = "center";
              ctx.textBaseline = "middle";
              ctx.fillText(label, node.x, node.y + nodeRadius + 10);
            }}
          />
        </div>


        {/* ✅ LEGEND */}
        <div className="absolute bottom-4 left-4 bg-white p-3 rounded shadow-lg text-xs border border-gray-300">
          <p className="font-semibold mb-2">Legend:</p>
          <p>
            <span className="inline-block w-3 h-3 bg-green-500 mr-2 rounded-full"></span>
            Origin
          </p>
          <p>
            <span className="inline-block w-3 h-3 bg-blue-500 mr-2 rounded-full"></span>
            Intermediary
          </p>
          <p>
            <span className="inline-block w-3 h-3 bg-red-500 mr-2 rounded-full"></span>
            Final Destination
          </p>
        </div>
      </div>
    </div>
  );
}


