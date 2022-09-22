from causaldag import DAG
import random
import networkx as nx

from collections import defaultdict
import math
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
Maintain a queue of (bounded) size interventions, skipping interventions if all incident edges already oriented.
If queue is empty, gather 1/2-clique separators from each connected component of size >= 2, and attempt to orient them.
To orient the union of 1/2-clique separator nodes Q, use atomic interventions if k = 1 or |Q| = 1, else compute the labelling scheme of Lemma 1 of [SKDV15].

The following few lines are copied from the proof of Lemma 1
Let n = p_d a^d + r_d and n = p_{d-1} a^{d-1} + r_{d-1}
1) Repeat 0 a^{d-1} times, repeat the next integer 1 a^{d-1} times and so on circularly from {0,1,...,a-1} till p_d * a^d.
2) After that, repeat 0 ceil(r_d/a) times followed by 1 ceil(r_d/a) times till we reach the nth position. Clearly, n-th integer in the sequence would not exceed a-1.
3) Every integer occurring after the position a^{d-1} p_{d-1} is increased by 1.
'''
def separator_policy(dag: DAG, k: int, verbose: bool = False) -> set:
    intervened_nodes = set()

    current_cpdag = dag.cpdag()

    intervention_queue = []
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
        while len(intervention_queue) > 0 and intervention is None:
            intervention = intervention_queue.pop()
    
            # If all incident edges already oriented, skip this intervention
            if sum([G.degree[node] for node in intervention]) == 0:
                intervention = None

        if intervention is None:
            assert len(intervention_queue) == 0

            # Compute 1/2-clique separator for each connected component of size >= 2
            clique_separator_nodes = []
            for cc_nodes in nx.connected_components(G):
                if len(cc_nodes) == 1:
                    continue
                cc = G.subgraph(cc_nodes)
                
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

                # Compute clique separator for this connected component then add to the list
                clique_separator_nodes += [unmap_indices[v] for v in compute_clique_graph_separator(adj_list, nodes)]

            assert len(clique_separator_nodes) > 0
            if k == 1 or len(clique_separator_nodes) == 1:
                intervention_queue = [set([v]) for v in clique_separator_nodes]
            else:
                # Setup parameters. Note that [SKDV15] use n and x+1 instead of h and L
                h = len(clique_separator_nodes)
                k_prime = min(k, h/2)
                a = math.ceil(h/k_prime)
                assert a >= 2
                L = math.ceil(math.log(h,a))
                assert pow(a,L-1) < h and h <= pow(a,L)

                # Execute labelling scheme
                S = defaultdict(set)
                for d in range(1, L+1):
                    a_d = pow(a,d)
                    r_d = h % a_d
                    p_d = h // a_d
                    a_dminus1 = pow(a,d-1)
                    r_dminus1 = h % a_dminus1 # Unused
                    p_dminus1 = h // a_dminus1
                    assert h == p_d * a_d + r_d
                    assert h == p_dminus1 * a_dminus1 + r_dminus1
                    for i in range(1, h+1):
                        node = clique_separator_nodes[i-1]
                        if i <= p_d * a_d:
                            val = (i % a_d) // a_dminus1
                        else:
                            val = (i - p_d * a_d) // math.ceil(r_d / a)
                        if i > a_dminus1 * p_dminus1:
                            val += 1
                        S[(d,val)].add(node)

                # Store output
                intervention_queue = list(S.values())
            assert len(intervention_queue) > 0    
            intervention = intervention_queue.pop()

        # Intervene on selected node(s) and update the CPDAG
        assert intervention is not None
        assert len(intervention) <= k
        intervention = frozenset(intervention)
        intervened_nodes.add(intervention)
        current_cpdag = current_cpdag.interventional_cpdag(dag, intervention)

    return intervened_nodes
