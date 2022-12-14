from dag_loader import DagSampler
from plot_results_vary_nnodes import plot_results_vary_nodes

algs = [
    'separator_k1',
    'separator_k2',
    'separator_k3',
    'separator_k5'
]
nnodes_list = list(range(10, 101, 5))
plot_results_vary_nodes(
    nnodes_list,
    100,
    DagSampler.SHANMUGAM,
    dict(density=.1, figname="exp4"),
    algorithms=algs,
    overwrite=True
)

