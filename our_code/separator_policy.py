from causaldag import DAG
import random
import networkx as nx

import sys
sys.path.insert(0, './PADS')
import LexBFS

'''
Verify that the peo computed is valid
For any node v, all neighbors that appear AFTER v forms a clique (i.e. pairwise adjacent)
'''
def verify_peo(adj_list, actual_to_peo, peo_to_actual):
    assert len(adj_list) == len(actual_to_peo)
    assert len(adj_list) == len(peo_to_actual)
    try:
        n = len(adj_list)
        for i in range(n):
            v = peo_to_actual[i]
            later_neighbors = [u for u in adj_list[v] if actual_to_peo[u] > i]
            for u in later_neighbors:
                for w in later_neighbors:
                    assert u == w or u in adj_list[w]
    except Exception as err:
        print('verification error:', adj_list, actual_to_peo, peo_to_actual)
        assert False

'''
Compute perfect elimination ordering using PADS
Source: https://www.ics.uci.edu/~eppstein/PADS/ABOUT-PADS.txt
'''
def peo(adj_list, nodes):
    n = len(nodes)

    G = dict()
    for v in nodes:
        G[v] = adj_list[v]
    lexbfs_output = list(LexBFS.LexBFS(G))

    # Reverse computed ordering to get actual perfect elimination ordering
    output = lexbfs_output[::-1]
    
    actual_to_peo = dict()
    peo_to_actual = dict()
    for i in range(n):
        peo_to_actual[i] = output[i]
        actual_to_peo[output[i]] = i

    # Sanity check: verify PADS's peo output
    # Can comment out for computational speedup
    #verify_peo(adj_list, actual_to_peo, peo_to_actual)
    
    return actual_to_peo, peo_to_actual

'''
Given a connected chordal graph on n nodes, compute the 1/2-clique graph separator
FAST CHORDAL SEPARATOR algorithm of [GRE84]
Reference: [GRE84] A Separator Theorem for Chordal Graphs
'''
def compute_clique_graph_separator(adj_list, nodes):
    n = len(nodes)

    # Compute perfect elimination ordering via lex bfs
    actual_to_peo, peo_to_actual = peo(adj_list, nodes)

    w = [1] * n
    total_weight = sum(w)

    # Compute separator
    peo_i = 0
    while w[peo_i] <= total_weight/2:
        # w[i] is the weight of the connected component of {v_0, ..., v_i} that contains v_i
        # v_k <- lowest numbered neighbor of v_i with k > i
        k = None
        for j in adj_list[peo_to_actual[peo_i]]:
            if actual_to_peo[j] > peo_i and (k is None or actual_to_peo[j] < actual_to_peo[k]):
                k = j
        if k is not None:
            w[actual_to_peo[k]] += w[peo_i]
        peo_i += 1

    # i is the minimum such that some component of {v_0, ..., v_i} weighs more than total+weight/2
    # C <- v_i plus all of v_{i+1}, ..., v_n that are adjacent to v_i
    C = [peo_to_actual[peo_i]]
    for j in adj_list[peo_to_actual[peo_i]]:
        if actual_to_peo[j] > peo_i:
            C.append(j)
    return C

'''
Steps until fully oriented:
1) Compute a clique separator
2) Partition the clique into disjoint subcliques of n/k vertices arbitrarily
3) To ensure that cut edges are oriented, intervene on all vertices in each subclique, one subclique at a time
4) For each subclique, pick each vertex with probability 1/2 independently and uniformly at random
5) Intervened on chosen vertices in 4). Repeat until subclique is fully oriented.

Phase 1: steps 1,2
Phase 2: step 3
Phase 3: steps 4,5

When k = 1, the algorithm performs atomic intervention as expected 
- the subcliques are just one vertex each
- phase 2 will intervene one vertex at a time as long as the vertex is adjacent to unoriented edges
- phase 3 will be skipped because a singleton subclique has no internal edges
'''
def separator_policy(dag: DAG, k: int, verbose: bool = False) -> set:
    intervened_nodes = set()

    current_cpdag = dag.cpdag()

    phase = 1
    subcliques = []
    subclique_idx = 0
    while current_cpdag.num_arcs != dag.num_arcs:
        if verbose: print(f"Remaining edges: {current_cpdag.num_edges}")
        
        node_to_intervene = None
        undirected_portions = current_cpdag.copy()
        undirected_portions.remove_all_arcs()

        # Cannot directly use G = undirected_portions.to_nx() because it does not first add the nodes
        # We need to first add nodes because we want to check if the clique nodes have incident edges
        # See https://causaldag.readthedocs.io/en/latest/_modules/causaldag/classes/pdag.html#PDAG 
        G = nx.Graph()
        G.add_nodes_from(undirected_portions.nodes)
        G.add_edges_from(undirected_portions.edges)

        intervention = None
        while intervention is None:
            # Phase 1
            # Step 1: Compute a clique separator
            # Step 2: Partition the clique into disjoint subcliques of n/k vertices arbitrarily
            if phase == 1:
                # Focus on any connected component
                cc = G.subgraph(max(nx.connected_components(G), key=len))

                # Map indices of subgraph into 0..n-1
                n = len(cc.nodes())
                map_indices = dict()
                unmap_indices = dict()
                for v in cc.nodes():
                    map_indices[v] = len(map_indices)
                    unmap_indices[map_indices[v]] = v

                # Extract adj_list and nodes of subgraph
                nodes = []
                adj_list = []
                for v, nbr_dict in cc.adjacency():
                    nodes.append(map_indices[v])
                    adj_list.append([map_indices[x] for x in list(nbr_dict.keys())])

                # Extract nodes from clique separator
                clique_nodes = compute_clique_graph_separator(adj_list, nodes)
                clique_nodes = [unmap_indices[v] for v in clique_nodes]

                # Partition clique nodes into groups of size <= k arbitrarily
                subcliques = [clique_nodes[i*k:(i+1)*k] for i in range((len(clique_nodes)+k-1)//k)]
                subclique_idx = 0
                phase = 2

            # Phase 2
            # Step 3: To ensure that cut edges are oriented, intervene on all vertices in each subclique, one subclique at a time
            if phase == 2:
                while intervention is None and subclique_idx < len(subcliques):
                    # Intervene on entire subclique if it is yet to be fully oriented
                    subclique_nodes = subcliques[subclique_idx]
                    if sum([G.degree[node] for node in subclique_nodes]) > 0:
                        intervention = subcliques[subclique_idx]
                    subclique_idx += 1
                if intervention is None:
                    subclique_idx = 0
                    phase = 3

            # Phase 3
            # Step 4: For each subclique, pick each vertex with probability 1/2 independently and uniformly at random
            # Step 5: Intervened on chosen vertices in 4). Repeat until subclique is fully oriented.
            if phase == 3:
                while intervention is None and subclique_idx < len(subcliques):
                    # If already fully oriented, skip this subclique
                    subclique_nodes = subcliques[subclique_idx]
                    if sum([G.degree[node] for node in subclique_nodes]) == 0:
                        subclique_idx += 1
                    else:
                        # Pick each vertex with probability 1/2 independently and uniformly at random
                        subclique_nodes = subcliques[subclique_idx]
                        chance = [random.random() for _ in range(len(subclique_nodes))]
                        intervention = [subclique_nodes[i] for i in range(len(subclique_nodes)) if chance[i] > 0.5]
                if intervention is None:
                    phase = 1

        # Intervene on selected node(s) and update the CPDAG
        assert intervention is not None
        intervention = frozenset(intervention)
        intervened_nodes.add(intervention)
        current_cpdag = current_cpdag.interventional_cpdag(dag, intervention)

    return intervened_nodes
