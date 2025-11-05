
python lora_train.py \
    --base_model '../qwen25_7b_instruct/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28' \
    --data_path './commonsense_170k.json' \
    --output_dir '../qwen25_7b_instruct/qwen25_7b_ceval_g256_lora16/train_output0912' \
    --batch_size 2  --micro_batch_size 2 --num_epochs 3 \
    --lora_r 16 --lora_alpha 16 \
    --learning_rate 2e-5 --cutoff_len 256 --val_set_size 10 \
    --eval_step 80 --save_step 80  --adapter_name dora \
    --target_modules '["q_proj", "k_proj", "v_proj", "up_proj", "down_proj"]' \
    --use_gradient_checkpointing