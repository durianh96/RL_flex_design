#!/bin/bash

#tarcs=(16 18 20 22 24)
tarcs=(27 28 29 30 31 32)
for (( i=0; i<${#tarcs[@]}; i++ )); do
python -m spinup.run_simple \
    --algo ppo  \
    --env_name Flexibility10x10T"${tarcs[i]}"_SP50-v0 \
    --exp_name F10x10T"${tarcs[i]}"_SP50_PPO_CH1024-128_SPE12000_ITR80_EP1000_ET0-2_ENV2  \
    --cpu 8 \
    --epochs 400  \
    --steps_per_epoch 12000  \
    --save_freq 10  \
    --custom_h 1024-128 \
    --act tf.nn.relu  \
    --eval_temp 0.2 \
    --env_version 2 \
    --num_runs 1 \
    --do_checkpoint_eval; done