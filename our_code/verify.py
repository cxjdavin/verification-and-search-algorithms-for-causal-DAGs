import causaldag as cd
import random
import networkx as nx
from networkx.algorithms import bipartite

'''
Given a directed graph G (networkx graph object), output the set of edges that are covered edges.
'''
def compute_covered_edges(G):
    covered_edges = []
    for u,v in G.edges:
        u_parents = set(G.predecessors(u))
        v_parents = set(G.predecessors(v))
        v_parents.remove(u)
        if u_parents == v_parents:
            covered_edges.append((u,v))
    return set(covered_edges)

'''
Given an undirected graph H (networkx graph object), output the minimum vertex cover.
Since H is a forest (and hence is bipartite), we can use Konig's theorem to compute the minimum vertex cover.
However, networkx requires us to process connected components one at a time.
Konig's theorem: In bipartite graph, size maximum matching = size of minimum vertex cover.
'''
def compute_minimum_vertex_cover(H):
    assert bipartite.is_bipartite(H)
    mvc = set()
    for V in nx.connected_components(H):
        cc = H.subgraph(V)
        assert bipartite.is_bipartite(cc)
        matching_for_cc = nx.bipartite.eppstein_matching(cc)
        mvc_for_cc = nx.bipartite.to_vertex_cover(cc, matching_for_cc)
        mvc.update(mvc_for_cc)
    assert is_vertex_cover(H, mvc)
    return mvc

'''
Given a graph G and a set vc of vertices, return whether vc is a vertex cover of G.
'''
def is_vertex_cover(G, vc):
    is_valid = True
    for u,v in G.edges:
        is_valid = is_valid and (u in vc or v in vc)
    return is_valid

'''
Given a DAG, compute a minimum vertex cover of the covered edges in the ground truth DAG
Note that this is *not* a search algorithm but a verification algorithm.
The input to this algorithm is the ground truth dag instead of the essential graph dag.cpdag()
'''
def atomic_verification(G):
    # Compute covered edges of ground truth
    covered_edges = compute_covered_edges(G)

    # Define H as the subgraph induced by the covered edges
    H = nx.Graph()
    H.add_edges_from(covered_edges)

    # Compute minimum vertex cover on H
    mvc = compute_minimum_vertex_cover(H)

    return mvc

'''
Given graph G and subset of vertices I, determine whether I is an atomic intervention set that fully orients essential graph of G.
'''
def validate(G, I):
    dag = cd.DAG.from_nx(G)
    cpdag = dag.interventional_cpdag([{node} for node in I], cpdag=dag.cpdag())
    assert cpdag.num_edges == 0
    print("Validated that {0} fully orients essential graph".format(I))

'''
Given graph G, compute verifying set I and check if it indeeds fully orients essential graph G.
Print it out so that we can manually check that it outputs the vertices that we expect.
On odd-sized cliques, it should output even-indices.
On trees, it should output just the root.
On tree skeletoned graphs, it should ignore v-structures and arcs that are oriented due to v-structures.
'''
def check_graph(G, name):
    I = atomic_verification(G)
    print("For {0}, we use {1} interventions: {2}".format(name, len(I), I))
    validate(G, I)

if __name__ == "__main__":
    # Windmill graph G^* from Appendix C
    # a,b,c,d,e,f,g,h are mapped to 0,1,2,3,4,5,6,7
    windmill = nx.DiGraph()
    windmill.add_nodes_from(list(range(8)))
    windmill.add_edges_from([(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(1,2),(3,4),(5,6),(7,0)])
    check_graph(windmill, "windmill")

    # Clique on 149 nodes
    clique149 = nx.complete_graph(149)
    directed_clique149 = nx.DiGraph([(u,v) for (u,v) in clique49.edges() if u < v])
    check_graph(directed_clique149, "clique on 149 nodes")
    
    # Clique on 150 nodes
    clique150 = nx.complete_graph(150)
    directed_clique150 = nx.DiGraph([(u,v) for (u,v) in clique150.edges() if u < v])
    check_graph(directed_clique150, "clique on 150 nodes")

    # Random tree on 100 nodes: Generate random tree skeleton then BFS from vertex 0
    tree = nx.random_tree(100)
    directed_tree = nx.bfs_tree(tree, 0)
    check_graph(directed_tree, "tree with root 0")

    # Random graph with tree skeleton on 100 nodes
    tree = nx.random_tree(100)
    directed_tree = nx.DiGraph([(u,v) for (u,v) in tree.edges() if u < v])
    check_graph(directed_tree, "tree skeleton")

