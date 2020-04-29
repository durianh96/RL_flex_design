#!/bin/bash

python -m spinup.run_flexibility                             --algo ppo                              --env_name F10x10b-v4                             --exp_name F10x10b_CH1024-128_ENV4                              --cpu 2                             --epochs 400                              --custom_h 1024-128                             --env_version 4                             --env_input input_ran10x10b_cv0.8.pkl                             --target_arcs  16 19                              --num_runs 4                             --save_freq 8                              --steps_per_epoch 24000                             --do_checkpoint_eval;