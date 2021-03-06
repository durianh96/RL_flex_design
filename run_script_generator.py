import argparse
from spinup.FlexibilityEnv_input.inputload import load_FlexibilityEnv_input
from spinup.run_flexibility import run_experiment
from multiprocessing import Process
import os
import numpy as np
import statistics


def _get_full_path(env_input):
    prefix = os.getcwd().split('RL_flex_design')[0]
    return prefix + "RL_flex_design/spinup/FlexibilityEnv_input/{}".format(env_input)


def get_tars_list(num_tars_per_script, target_arcs):
    list_tars = []
    count = 0
    while (count + 1) * num_tars_per_script < len(target_arcs):
        list_tars.append(target_arcs[count * num_tars_per_script: (count + 1) * num_tars_per_script])
        count += 1
    list_tars.append(target_arcs[count * num_tars_per_script:])
    return list_tars


def _get_target_arcs_string(target_arcs):
    string = ''
    for tar in target_arcs:
        string += '{} '.format(tar)

    return string


def make_executable(path):
    mode = os.stat(path).st_mode
    mode |= (mode & 0o444) >> 2  # copy R bits to X
    os.chmod(path, mode)


def _get_seed_str(starting_seed, num_runs):
    seed_str = ""

    for i in range(num_runs):
        seed_str += "{} ".format(starting_seed + i * 10)

    return seed_str.strip()


def get_input(experiment):
    if '-' in experiment:
        exp = experiment.split('-')[0]
    else:
        exp = experiment
    return INPUTS[exp]


# INPUTS = {'10x10b': 'input_ran10x10b_cv0.8.pkl'}

from spinup.FlexibilityEnv_input.FlexibilityEnv_INPUTS import INPUTS


def generate_scripts_for_multiple_target_arcs(experiment, env_input, env_version_list, epoch_episodes,
                                              num_tars_per_script, num_batches, num_runs, gamma=None, lam=None,
                                              variance_reduction=False, env_n_sample=50, custom_h=None,
                                              cpu=2, tar_list=None,
                                              early_stop=None,
                                              epoch=800,
                                              save_freq=10,
                                              save_all_eval=None,
                                              included_tars=None):
    m, n, mean_c, mean_d, sd_d, profit_mat, target_arcs, fixed_costs, flex_0 = load_FlexibilityEnv_input(
        _get_full_path(env_input))
    print("number of existing arcs {}".format(flex_0.sum()))

    if included_tars is not None:
        # filter out tars that is not in included_tars
        target_arcs = [tar for tar in target_arcs if tar in included_tars]

    if tar_list is None or (tar_list is not None and len(tar_list) == 0):
        tar_list = get_tars_list(num_tars_per_script, target_arcs)

    print("target arcs to be run: {}".format(tar_list))

    for batch in range(num_batches):
        starting_seed = 100 * batch
        for env_version in env_version_list:
            # create entrypoint script
            # !/bin/bash
            path = 'run_{}_ENV{}_batch{}_entrypoint.sh'.format(experiment, env_version, batch)
            python_string = 'for((i=0;i < {};i++)); do bash run_{}_ENV{}_batch{}_'.format(len(tar_list),
                                                                                          experiment,
                                                                                          env_version,
                                                                                          batch) \
                            + '$' + '{' + 'i' + '}' + '.sh & done'
            with open(path, 'w') as f:
                f.write('#!/bin/bash\n\n')
                f.write(python_string)
            make_executable(path)

            print(python_string)

            # create scripts to be called in parallel
            for idx, target_arcs in enumerate(tar_list):

                assert len(target_arcs) >= 1
                if len(target_arcs) == 1:
                    # add 'tar' to exp_name explicitely
                    exp_name = 'F{}_CH{}_ENV{}_tar{}'.format(experiment,
                                                             '1024-128' if custom_h is None else custom_h,
                                                             env_version,
                                                             target_arcs[0])
                else:
                    exp_name = 'F{}_CH{}_ENV{}'.format(experiment,
                                                       '1024-128' if custom_h is None else custom_h,
                                                       env_version)

                python_string = "python -m spinup.run_flexibility   \\\n   \
                                --algo ppo    \\\n   \
                                --env_name F{}-v{}   \\\n   \
                                --exp_name {}    \\\n   \
                                --cpu {}   \\\n   \
                                --epochs {}    \\\n   \
                                --custom_h 1024-128   \\\n   \
                                --env_version {}   \\\n   \
                                --env_input {}   \\\n   \
                                --target_arcs  {}   \\\n   \
                                --seed {}   \\\n   \
                                --save_freq {}    \\\n   \
                                --steps_per_epoch {}   \\\n   \
                                --do_checkpoint_eval  \\\n".format(
                    experiment,
                    env_version,
                    exp_name,
                    cpu,
                    epoch,
                    env_version,
                    env_input,
                    _get_target_arcs_string(target_arcs),
                    _get_seed_str(starting_seed, num_runs),
                    save_freq,
                    int(np.ceil((int(statistics.mean(target_arcs)) - flex_0.sum()) * epoch_episodes))
                )

                if variance_reduction:
                    python_string += '                                   --env_subtract_full_flex  \\\n'

                if env_n_sample != 50:
                    python_string += '                                   --env_n_sample {}  \\\n'.format(env_n_sample)

                if custom_h is not None:
                    python_string += '                                   --custom_h {}   \\\n'.format(custom_h)

                if early_stop is not None:
                    python_string += '                                   --early_stop {}  \\\n'.format(early_stop)

                if save_all_eval is not None:
                    python_string += '                                   --save_all_eval  \\\n'

                if gamma is not None:
                    python_string += '                                   --gamma {}   \\\n'.format(gamma)

                if lam is None:
                    python_string += '                                   ;'
                else:
                    python_string += '                                   --lam {};'.format(lam)

                path = 'run_{}_ENV{}_batch{}_{}.sh'.format(experiment, env_version, batch, idx)
                with open(path, 'w') as f:
                    f.write('#!/bin/bash\n\n')
                    f.write(python_string)

                make_executable(path)

                print(python_string)


def generate_scripts_for_one_target_arcs(experiment, env_input, env_version_list, epoch_episodes, target_arcs,
                                         num_runs, starting_seed, gamma=None, lam=None,
                                         variance_reduction=False, env_n_sample=50,
                                         early_stop=None, cpu=8, epoch=800, save_freq=10, save_all_eval=None,
                                         custom_h=None, meta_learning=False, finetune=False, finetune_path=None,
                                         finetune_meta_trained_epoch=None):
    m, n, mean_c, mean_d, sd_d, profit_mat, _, fixed_costs, flex_0 = load_FlexibilityEnv_input(
        _get_full_path(env_input))
    print("number of existing arcs {}".format(flex_0.sum()))

    target_arcs_in_names = 0 if meta_learning else target_arcs

    for env_version in env_version_list:
        # create entrypoint script
        # !/bin/bash
        path = 'run_{}_ENV{}_tar{}_entrypoint.sh'.format(experiment, env_version, target_arcs_in_names)
        python_string = 'for((i=0;i < {};i++)); do bash run_{}_ENV{}_tar{}_'.format(num_runs,
                                                                                    experiment,
                                                                                    env_version,
                                                                                    target_arcs_in_names) \
                        + '$' + '{' + 'i' + '}' + '.sh & done'
        with open(path, 'w') as f:
            f.write('#!/bin/bash\n\n')
            f.write(python_string)
        make_executable(path)

        print(python_string)

        # create scripts to be called in parallel
        for idx in range(num_runs):

            target_arcs = target_arcs if meta_learning is False else (13 if idx % 2 == 1 else 22)

            python_string = "python -m spinup.run_flexibility  \\\n \
                            --algo ppo  \\\n \
                            --env_name F{}-v{}  \\\n \
                            --exp_name F{}_CH{}_ENV{}_tar{}  \\\n \
                            --cpu {} \\\n \
                            --epochs {}  \\\n \
                            --custom_h 1024-128  \\\n \
                            --env_version {}  \\\n \
                            --env_input {}  \\\n \
                            --target_arcs  {}  \\\n \
                            --seed {}  \\\n \
                            --save_freq {}   \\\n \
                            --steps_per_epoch {}  \\\n \
                            --do_checkpoint_eval \\\n".format(
                experiment,
                env_version,
                experiment,
                '1024-128' if custom_h is None else custom_h,
                env_version,
                target_arcs_in_names,
                cpu,
                epoch,
                env_version,
                env_input,
                target_arcs if meta_learning is False else (13 if idx % 2 == 1 else 22),
                starting_seed + 10 * idx,
                save_freq,
                int(np.ceil(
                    (target_arcs - flex_0.sum()) * epoch_episodes)) if meta_learning is False else 20 * epoch_episodes
            )

            if variance_reduction:
                python_string += '                             --env_subtract_full_flex  \\\n'

            if env_n_sample != 50:
                python_string += '                             --env_n_sample {}  \\\n'.format(env_n_sample)

            if early_stop is not None:
                python_string += '                             --early_stop {}  \\\n'.format(early_stop)

            if save_all_eval is not None:
                python_string += '                             --save_all_eval  \\\n'

            if gamma is not None:
                python_string += '                             --gamma {}  \\\n'.format(gamma)

            if custom_h is not None:
                python_string += '                             --custom_h {}  \\\n'.format(custom_h)

            if meta_learning:
                python_string += '                             --meta_learning  \\\n'

            if finetune:
                python_string += '                             --finetune  \\\n'
                if finetune_meta_trained_epoch is None:
                    python_string += '                             --finetune_model_path {}  \\\n'.format(
                        '{}_s{}'.format(finetune_path, starting_seed + 10 * idx))
                else:
                    python_string += '                             --finetune_model_path {}  \\\n'.format(
                        '{}_s{}/simple_save{}'.format(finetune_path,
                                                       starting_seed + 10 * idx,
                                                       finetune_meta_trained_epoch))

            if lam is None:
                python_string += '                             ;'
            else:
                python_string += '                             --lam {};'.format(lam)

            path = 'run_{}_ENV{}_tar{}_{}.sh'.format(experiment, env_version, target_arcs_in_names, idx)
            with open(path, 'w') as f:
                f.write('#!/bin/bash\n\n')
                f.write(python_string)

            make_executable(path)

            print(python_string)


if __name__ == "__main__":
    # specify parameters
    experiment = '10x10a'
    env_input = get_input(experiment)
    epoch_episodes = 800
    # epoch_episodes = 1200
    gamma = 0.99
    lam = 0.999
    custom_h = '1640-332' if experiment == '10x26' else None  # use default 1024-512

    # parameters for Ablation Study
    env_version_list = [5]
    variance_reduction = True  # for this version of the paper, we do not use variance reduction, i.e., VR=False
    env_n_sample = 50  # also run for env_n_smaple = 1 and 20

    # append experiment name with VR and SP. Note that ENV is added to the exp_name later, so no need to add it here.
    if variance_reduction:
        experiment += "-VR"
    experiment += "-SP{}".format(env_n_sample)

    # ##### Generate scripts for a list of target_arcs. The list is divided into sub-lists
    # # each contains num_tar_per_script target_arcs.
    # num_tars_per_script = 1
    # # the number of entrypoints to be created with different seeds to do more parallelization
    # num_batches = 5
    # # the number of runs with different seed for each target arc
    # num_runs = 4
    #
    # # can also manually specify the target arcs list
    # cpu = 6
    # early_stop = 60
    # save_freq = 10
    # included_tars = [41, 44, 47]
    #
    # generate_scripts_for_multiple_target_arcs(experiment, env_input, env_version_list, epoch_episodes,
    #                                           num_tars_per_script, num_batches, num_runs, gamma, lam,
    #                                           variance_reduction, env_n_sample,
    #                                           custom_h=custom_h,
    #                                           cpu=cpu,
    #                                           early_stop=early_stop,
    #                                           save_freq=save_freq,
    #                                           included_tars=included_tars)

    ##### Generate scripts for one particular target_arcs but with different seeds, which will then be called in parallel
    # Used for Ablation Study
    target_arcs_list = [13]
    num_runs = 12

    for target_arcs in target_arcs_list:
        starting_seed = 0
        generate_scripts_for_one_target_arcs(experiment, env_input, env_version_list, epoch_episodes,
                                             target_arcs, num_runs, starting_seed, gamma, lam,
                                             variance_reduction, env_n_sample,
                                             custom_h=custom_h)

    # ##### Generate scripts for plotting training curve with progress_eval.txt
    # early_stop = -1
    # epoch = 200
    # target_arcs_list = [13, 22]
    # save_freq = 10
    # save_all_eval = True
    #
    # for target_arcs in target_arcs_list:
    #     num_runs = 12
    #     starting_seed = 800000
    #     generate_scripts_for_one_target_arcs(experiment, env_input, env_version_list, epoch_episodes,
    #                                          target_arcs, num_runs, starting_seed, gamma, lam,
    #                                          variance_reduction, env_n_sample,
    #                                          early_stop=early_stop,
    #                                          epoch=epoch,
    #                                          save_freq=save_freq,
    #                                          save_all_eval=save_all_eval,
    #                                          custom_h=custom_h)

    # # ##### Generate scripts for meta_learning training
    # # During meta training target_arcs are random.
    # # During evaluation, we fix target_arcs to 13 or 22, so that we can see how well the meta learnt model
    # # solves a particular problem
    # target_arcs = None
    # meta_learning = True
    # num_runs = 12
    # early_stop = 30
    # epoch_episodes = 1200
    # experiment += '-META'
    #
    # starting_seed = 0
    # generate_scripts_for_one_target_arcs(experiment, env_input, env_version_list, epoch_episodes,
    #                                      target_arcs, num_runs, starting_seed, gamma, lam,
    #                                      variance_reduction, env_n_sample, custom_h=custom_h,
    #                                      early_stop=early_stop,
    #                                      meta_learning=meta_learning)

    # # ##### Generate scripts for meta_learning finetuning
    # target_arcs_list = [13, 22]
    # num_runs = 12
    # early_stop = 60
    # epoch_episodes = 800
    # finetune = True
    # finetune_meta_trained_epoch = 100
    # finetune_path = '/home/user/git/RL_flex_design/data/F10x10a-SP50-META_CH1024-128_ENV5_tar0/F10x10a-SP50-META_CH1024-128_ENV5_tar0'
    # experiment += '-Finetune'
    # if finetune_meta_trained_epoch:
    #     experiment += 'Meta{}'.format(finetune_meta_trained_epoch)
    #
    #
    # starting_seed = 0
    #
    # for target_arcs in target_arcs_list:
    #     generate_scripts_for_one_target_arcs(experiment, env_input, env_version_list, epoch_episodes,
    #                                          target_arcs, num_runs, starting_seed, gamma, lam,
    #                                          variance_reduction, env_n_sample, custom_h=custom_h,
    #                                          early_stop=early_stop,
    #                                          finetune=finetune,
    #                                          finetune_path=finetune_path,
    #                                          finetune_meta_trained_epoch=finetune_meta_trained_epoch)
