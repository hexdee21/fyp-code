import React from "react";
import ForceGraph2D from "react-force-graph-2d";

export default function GraphModal({ tx, graphData, onClose }) {
  if (!tx) return null;

  // Extract transaction data
  const txData = tx.tx || tx;
  const path = txData.path || [txData.sender, txData.receiver];

  return (
    <div className="fixed inset-0 bg-[#0f0f1f] bg-opacity-95 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
      
      {/* Main Modal Box - Added 'relative' here to act as anchor for legend */}
      <div className="relative bg-[#111128] border border-[#00ffff] shadow-[0_0_30px_#00ffff44] rounded-lg w-[95vw] h-[85vh] p-4 text-neon">
        
        {/* Close Button */}
        <button
          className="absolute top-3 right-4 text-2xl font-bold text-red-500 hover:text-[#00ffff] transition-colors z-20"
          onClick={onClose}
        >
          ✕
        </button>

        {/* Heading */}
        <h2 className="text-xl font-bold text-center mb-3 text-[#00ffff] drop-shadow-[0_0_5px_#00ffff]">
          Transaction Graph
        </h2>

        {/* Full Path Display */}
        <div className="text-center mb-3 bg-[#1a1a2e] p-3 rounded border border-[#00ffff33]">
          <p className="font-semibold text-base mb-1 text-gray-300">
            📍 Full Transaction Path ({path.length} accounts)
          </p>
          <p className="text-sm font-mono break-all text-[#00ffff]">
            {path.join(" → ")}
          </p>
        </div>

        {/* Transaction Details */}
        <div className="text-center text-gray-300 mb-4 text-sm">
          <div className="flex justify-center gap-4 flex-wrap">
            <span><b>Origin:</b> <span className="text-[#00ffff]">{path[0] || txData.sender}</span></span>
            <span><b>Destination:</b> <span className="text-[#00ffff]">{path[path.length - 1] || txData.receiver}</span></span>
            <span><b>Amount:</b> <span className="text-[#00ffff]">${txData.amount?.toLocaleString()}</span></span>
            {txData.total_amount && txData.total_amount !== txData.amount && (
              <span className="text-orange-400">
                <b>Total (all hops):</b> ${txData.total_amount?.toLocaleString()}
              </span>
            )}
          </div>
        </div>

        {/* Layering Warning */}
        {txData.num_layers > 0 && (
          <div className="text-center text-xs text-gray-300 mb-3 bg-[#2a1a1a] p-2 rounded border border-red-500/50">
            <span className="font-bold text-red-500">⚠️ Layering Detected:</span>
            {" "}
            <span>Layers: {txData.num_layers}</span> |
            <span> Accounts: {txData.num_accounts_involved}</span> |
            <span> Avg Delay: {txData.avg_delay_between_layers?.toFixed(2)}s</span>
          </div>
        )}

        {/* Graph Container */}
        {/* NOTE: Removed 'relative' from here, as the modal is now the relative parent */}
        <div className="border border-[#00ffff33] rounded bg-[#1a1a2e] overflow-hidden w-full h-[55vh]">
          
          <ForceGraph2D
            graphData={graphData}
            width={window.innerWidth * 0.9}
            height={window.innerHeight * 0.55}
            nodeRelSize={8}
            backgroundColor="#1a1a2e" 
            linkDirectionalArrowLength={8}
            linkDirectionalArrowRelPos={1}
            linkColor={() => "#00ffff66"} 
            linkWidth={2}
            nodeCanvasObject={(node, ctx, scale) => {
              const label = node.id;
              const fontSize = 14 / scale;
              const nodeRadius = 6;
              
              ctx.beginPath();
              ctx.arc(node.x, node.y, nodeRadius, 0, 2 * Math.PI);
              ctx.fillStyle = node.color || "blue";
              ctx.fill();
              ctx.strokeStyle = "#fff";
              ctx.lineWidth = 2;
              ctx.stroke();
              
              ctx.font = `${fontSize}px Sans-Serif`;
              ctx.fillStyle = "#00ffff"; 
              ctx.textAlign = "center";
              ctx.textBaseline = "middle";
              ctx.shadowColor = "#00ffff";
              ctx.shadowBlur = 4;
              ctx.fillText(label, node.x, node.y + nodeRadius + 10);
              ctx.shadowBlur = 0;
            }}
          />
        </div>

        {/* ✅ FIXED LEGEND BOX - Moved outside graph container, high z-index, bright text */}
        <div className="absolute bottom-6 left-6 bg-[#111128] p-3 rounded border border-[#00ffff] shadow-[0_0_15px_#00ffff33] z-50">
            <p className="font-bold mb-2 text-[#00ffff] border-b border-[#00ffff33] pb-1">Legend</p>
            
            <div className="flex items-center mb-2">
              <span className="w-3 h-3 bg-green-500 rounded-full mr-2 shadow-[0_0_8px_#22c55e]"></span>
              {/* Explicit white text for maximum visibility */}
              <span className="text-white text-xs font-semibold">Origin</span>
            </div>

            <div className="flex items-center mb-2">
              <span className="w-3 h-3 bg-blue-500 rounded-full mr-2 shadow-[0_0_8px_#3b82f6]"></span>
              <span className="text-white text-xs font-semibold">Intermediary</span>
            </div>

            <div className="flex items-center">
              <span className="w-3 h-3 bg-red-500 rounded-full mr-2 shadow-[0_0_8px_#ef4444]"></span>
              <span className="text-white text-xs font-semibold">Final Destination</span>
            </div>
          </div>

      </div>
    </div>
  );
}

