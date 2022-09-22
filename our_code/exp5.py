from dag_loader import DagSampler
from plot_results_vary_nnodes import plot_results_vary_nodes

algs = [
    'separator_k1',
    'separator_k2',
    'separator_k3',
    'separator_k5'
]
nnodes_list = [100, 200, 300, 400, 500]
plot_results_vary_nodes(
    nnodes_list,
    100,
    DagSampler.HAIRBALL_PLUS,
    dict(degree=40, e_min=20, e_max=50, figname="exp5"),
    algorithms=algs,
    overwrite=True
)


