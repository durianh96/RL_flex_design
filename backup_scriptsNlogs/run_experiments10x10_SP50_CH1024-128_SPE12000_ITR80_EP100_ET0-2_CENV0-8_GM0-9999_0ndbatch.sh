#!/bin/bash

#tarcs=(9 10 11 12 13 14 15 16 17 18 19)
tarcs=(19)
for (( i=0; i<${#tarcs[@]}; i++ )); do
python -m spinup.run_simple \
    --algo ppo  \
    --env Flexibility10x10T"${tarcs[i]}"_SP50-v0 \
    --exp_name F10x10T"${tarcs[i]}"_SP50_PPO_CH1024-128_SPE12000_ITR80_EP150_ET0-2_CENV0-8_GM0-9999  \
    --cpu 8 \
    --epochs 150  \
    --steps_per_epoch 12000  \
    --save_freq 10  \
    --custom_h 1024-128 \
    --act tf.nn.relu  \
    --eval_temp 0.2 \
    --gamma 0.9999 \
    --do_checkpoint_eval; done