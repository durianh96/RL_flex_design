#!/bin/bash

python -m spinup.run_flexibility  \
                             --algo ppo  \
                             --env_name F8x16JG-SP50-v5  \
                             --exp_name F8x16JG-SP50_CH1024-128_ENV5_tar28  \
                             --cpu 8 \
                             --epochs 300  \
                             --custom_h 1024-128  \
                             --env_version 5  \
                             --env_input input_JGm8n16_cv0.8.pkl  \
                             --target_arcs  28  \
                             --seed 40  \
                             --save_freq 30   \
                             --steps_per_epoch 22400  \
                             --do_checkpoint_eval \
                             --early_stop 60  \
                             --save_all_eval  \
                             --gamma 0.99  \
                             --lam 0.999;