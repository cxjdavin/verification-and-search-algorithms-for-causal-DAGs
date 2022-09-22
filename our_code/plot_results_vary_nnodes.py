from dag_loader import DagSampler
import matplotlib.pyplot as plt
import seaborn as sns
from config import FIGURE_FOLDER, POLICY2COLOR, POLICY2LABEL
import os
import random
import ipdb
from result_getter import ResultGetter
sns.set()

OVERWRITE_ALL = True


def plot_results_vary_nodes(
        nnodes_list: list,
        ngraphs: int,
        sampler: DagSampler,
        other_params: dict,
        algorithms: set,
        overwrite=False
):
    random.seed(98625472)
    os.makedirs('figures', exist_ok=True)

    rg = ResultGetter(
        algorithms,
        nnodes_list,
        sampler,
        other_params_list=[other_params],
        ngraphs=ngraphs,
    )
    res_df = rg.get_results(overwrite=overwrite)
    mean_ratios = res_df.groupby(level=['alg', 'nnodes'])['regret_ratio'].mean()
    std_ratios = res_df.groupby(level=['alg', 'nnodes'])['regret_ratio'].std()
    max_ratios = res_df.groupby(level=['alg', 'nnodes'])['regret_ratio'].max()
    average_times = res_df.groupby(level=['alg', 'nnodes'])['time'].mean()
    std_times = res_df.groupby(level=['alg', 'nnodes'])['time'].std()
    mean_interventions = res_df.groupby(level=['alg', 'nnodes'])['interventions'].mean()
    std_interventions = res_df.groupby(level=['alg', 'nnodes'])['interventions'].std()

    algorithms = sorted(algorithms)

    plt.clf()
    for alg in algorithms:
        #plt.plot(nnodes_list, mean_ratios[mean_ratios.index.get_level_values('alg') == alg], color=POLICY2COLOR[alg], label=POLICY2LABEL[alg])
        plt.errorbar(nnodes_list, mean_ratios[mean_ratios.index.get_level_values('alg') == alg], color=POLICY2COLOR[alg], label=POLICY2LABEL[alg], yerr=std_ratios[std_ratios.index.get_level_values('alg') == alg], capsize=5)

    plt.xlabel('Number of Nodes')
    plt.ylabel('Average Competitive Ratio')
    plt.xticks(nnodes_list)
    plt.legend()
    other_params_str = ','.join((f"{k}={v}" for k, v in other_params.items()))
    #plt.savefig(os.path.join(FIGURE_FOLDER, f'avgregret_sampler={sampler},nnodes_list={nnodes_list},{other_params_str}.png'))
    #plt.savefig(os.path.join(FIGURE_FOLDER, f'avgregret'))
    plt.savefig(os.path.join(FIGURE_FOLDER, '{0}_avgcompratio.png'.format(other_params['figname'])))

    plt.clf()
    for alg in algorithms:
        plt.plot(nnodes_list, max_ratios[max_ratios.index.get_level_values('alg') == alg], color=POLICY2COLOR[alg], label=POLICY2LABEL[alg])

    plt.xlabel('Number of Nodes')
    plt.ylabel('Maximum Competitive Ratio')
    plt.legend()
    plt.xticks(nnodes_list)
    other_params_str = ','.join((f"{k}={v}" for k, v in other_params.items()))
    #plt.savefig(os.path.join(FIGURE_FOLDER, f'maxregret_sampler={sampler},nnodes_list={nnodes_list},{other_params_str}.png'))
    #plt.savefig(os.path.join(FIGURE_FOLDER, f'maxregret'))
    plt.savefig(os.path.join(FIGURE_FOLDER, '{0}_maxcompratio.png'.format(other_params['figname'])))

    plt.clf()
    for alg in algorithms:
        #plt.plot(nnodes_list, average_times[average_times.index.get_level_values('alg') == alg], color=POLICY2COLOR[alg], label=POLICY2LABEL[alg])
        plt.errorbar(nnodes_list, average_times[average_times.index.get_level_values('alg') == alg], color=POLICY2COLOR[alg], label=POLICY2LABEL[alg], yerr=std_times[std_times.index.get_level_values('alg') == alg], capsize=5)

    plt.xlabel('Number of Nodes')
    plt.ylabel('Average Computation Time')
    plt.legend()
    plt.yscale('log')
    plt.xticks(nnodes_list)
    other_params_str = ','.join((f"{k}={v}" for k, v in other_params.items()))
    #plt.savefig(os.path.join(FIGURE_FOLDER, f'times_sampler={sampler},nnodes_list={nnodes_list},{other_params_str}.png'))
    #plt.savefig(os.path.join(FIGURE_FOLDER, f'times'))
    plt.savefig(os.path.join(FIGURE_FOLDER, '{0}_time.png'.format(other_params['figname'])))

    plt.clf()
    for alg in algorithms:
        plt.errorbar(nnodes_list, mean_interventions[mean_interventions.index.get_level_values('alg') == alg], color=POLICY2COLOR[alg], label=POLICY2LABEL[alg], yerr=std_interventions[std_interventions.index.get_level_values('alg') == alg], capsize=5)

    plt.xlabel('Number of Nodes')
    plt.ylabel('Average number of interventions used')
    plt.legend()
    plt.xticks(nnodes_list)
    other_params_str = ','.join((f"{k}={v}" for k, v in other_params.items()))
    plt.savefig(os.path.join(FIGURE_FOLDER, '{0}_interventioncount.png'.format(other_params['figname'])))

    #ipdb.set_trace()
