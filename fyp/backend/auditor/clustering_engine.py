import pandas as pd
import networkx as nx
from networkx.algorithms import community

def cluster_wallets(transactions):
    """
    Takes a list of transactions:
    [{"from": "...", "to": "...", "value": 1.2}, ...]

    Returns clusters like:
    [{"cluster_id": 1, "addresses": [...], "size": N}, ...]
    """
    txs = pd.DataFrame(transactions)

    if txs.empty or "from" not in txs or "to" not in txs:
        return []

    # Build graph
    G = nx.Graph()
    for _, row in txs.iterrows():
        G.add_edge(row["from"], row["to"], weight=row.get("value", 1))

    # Find communities
    communities = list(community.greedy_modularity_communities(G))

    clusters = []
    for i, c in enumerate(communities):
        clusters.append({
            "cluster_id": i + 1,
            "addresses": list(c),
            "size": len(c)
        })
    return clusters
