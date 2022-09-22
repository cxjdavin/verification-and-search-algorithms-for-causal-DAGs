import itertools as itr
from dag_loader import DagLoader
from alg_runner import AlgRunner
import pandas as pd
import math

class ResultGetter:
    def __init__(self, algs, nnodes_list, sampler, other_params_list, ngraphs=100, comparable_edges=True):
        self.algs = algs
        self.nnodes_list = nnodes_list
        self.other_params_list = other_params_list
        self.sampler = sampler
        self.ngraphs = ngraphs
        self.dag_loaders = [
            DagLoader(nnodes, self.ngraphs, self.sampler, other_params, comparable_edges=comparable_edges)
            for nnodes, other_params in itr.product(self.nnodes_list, self.other_params_list)
        ]

    def get_results(self, overwrite=False):
        results = []

        for alg in self.algs:
            for dl in self.dag_loaders:
                ar = AlgRunner(alg, dl)
                nnodes_list, times_list = ar.get_alg_results(overwrite=overwrite)
                vo_list = dl.get_verification_optimal_ivs(overwrite=overwrite)

                # For k > 1, use LOWER BOUND v_k(G) >= ceil(v_1(G) / k) for ratio computation
                # For k = 1, v_k(G) = ceil(v_1(G) / k)
                if 'separator' in alg:
                    k = int(alg[-1])
                    vo_list = [math.ceil(v1/k) for v1 in vo_list]

                for nnodes, time, vo in zip(nnodes_list, times_list, vo_list):
                    results.append(dict(
                        alg=alg,
                        nnodes=dl.nnodes,
                        **dl.other_params,
                        interventions=nnodes,
                        time=time,
                        vo=vo
                    ))

        res_df = pd.DataFrame(results)
        res_df = res_df.set_index(list(set(res_df.columns) - {'interventions', 'time', 'vo'}))
        res_df['regret_ratio'] = res_df['interventions'] / res_df['vo']
        return res_df


