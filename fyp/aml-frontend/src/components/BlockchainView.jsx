export default function BlockchainView({ blocks, onSelectTx, loading }) {
  return (
    <div className="bg-white shadow p-4 rounded-lg">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold">Blockchain Blocks</h2>
        <span className="text-sm text-gray-500">
          {loading ? "Loading..." : `${blocks.length} blocks`}
        </span>
      </div>

      {blocks.length === 0 ? (
        <p className="text-gray-500">No blocks yet</p>
      ) : (
        <ul className="space-y-3 max-h-[500px] overflow-y-auto">
          {blocks.slice(-10).reverse().map((b, i) => (
            <li key={i} className="p-3 border rounded hover:bg-gray-50">
              <div className="text-sm">
                <b>Block #{b.index}</b> —{" "}
                {new Date((b.timestamp || Date.now()) * 1000).toLocaleString()}
              </div>

              <div className="text-xs text-gray-500 break-all">
                Hash: {b.hash}
              </div>

              <div className="mt-2 text-sm">
                <div className="font-semibold mb-1">
                  Transactions ({b.transactions?.length || 0})
                </div>

                {b.transactions?.length > 0 ? (
                  <ul className="pl-4 list-disc text-gray-700 text-xs space-y-1">
                    {b.transactions.map((tx, j) => (
                      <li
                        key={j}
                        className="cursor-pointer hover:underline"
                        onClick={() => onSelectTx(tx)}
                      >
                        {tx.sender} → {tx.receiver} ({tx.amount})
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-gray-400 text-xs italic">
                    No transactions
                  </p>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}



