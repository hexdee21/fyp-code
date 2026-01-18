export default function FlaggedTable({ flagged, onSelectTx }) {
  return (
    <div className="bg-white shadow p-4 rounded-lg">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold text-red-400 text-neon">Flagged Transactions</h2>
        <span className="text-sm text-gray-400">{flagged.length} flagged</span>
      </div>

      {flagged.length === 0 ? (
        <p className="text-gray-500">No suspicious activity detected</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-400 border-b">
              <th>Sender</th>
              <th>Receiver</th>
              <th>Amount</th>
              <th>Rules</th>
              <th>Action</th>
            </tr>
          </thead>

          <tbody>
            {flagged.map((f, idx) => (
              <tr key={idx} className="border-t hover:bg-[#111133]">
                <td>{f.sender ?? f.tx?.sender}</td>
                <td>{f.receiver ?? f.tx?.receiver}</td>
                <td>{f.amount ?? f.tx?.amount}</td>
                <td className="text-xs text-neon">
                  {(f.rules_triggered || f.matched_rules || [])?.slice(0, 3).join(", ")}
                </td>
                <td>
                  <button
                    onClick={() => onSelectTx(f)}
                    className="bg-blue-600 text-white px-3 py-1 rounded text-xs hover:bg-blue-700"
                  >
                    View Graph
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
