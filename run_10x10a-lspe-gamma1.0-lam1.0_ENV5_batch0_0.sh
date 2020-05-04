#!/bin/bash

python -m spinup.run_flexibility                                 --algo ppo                                  --env_name F10x10a-lspe-gamma1.0-lam1.0-v5                                 --exp_name F10x10a-lspe-gamma1.0-lam1.0_CH1024-128_ENV5                                  --cpu 2                                 --epochs 800                                  --custom_h 1024-128                                 --env_version 5                                 --env_input input_ran10x10a_cv0.8.pkl                                 --target_arcs  10 13 16                                  --seed 0 10 20 30                                 --save_freq 10                                  --steps_per_epoch 10400                                 --do_checkpoint_eval  --gamma 1.0    --lam 1.0;