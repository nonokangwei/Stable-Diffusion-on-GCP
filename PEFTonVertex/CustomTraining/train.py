import subprocess
import os
import argparse
import re
import torch
from safetensors.torch import save_file

def main(args):

    MODEL_NAME= args.model_name #"runwayml/stable-diffusion-v1-5"
    INSTANCE_DIR= args.input_storage
    OUTPUT_DIR= args.output_storage
    PROMPT = args.prompt
    CLASS_PROMP = args.class_prompt

    #subprocess.run("accelerate config update --config_file /content/accelerate_2.yaml", shell=True)
    os.chdir("/root/peft/examples/lora_dreambooth")

    # for complex commands, with many args, use string + `shell=True`:
    cmd_str = (f'accelerate launch train_dreambooth.py '
               f'--pretrained_model_name_or_path="{MODEL_NAME}" '
               f'--instance_data_dir="{INSTANCE_DIR}" '
               f'--output_dir="{OUTPUT_DIR}" '
               f'--train_text_encoder '
               f'--with_prior_preservation '
               f'--prior_loss_weight=1 '
               f'--num_class_images=50 '
               f'--class_prompt="{CLASS_PROMPT}" '
               f'--class_data_dir="{OUTPUT_DIR}/class_data" '
               f'--instance_prompt="{PROMPT}" '
               f'--use_lora '
               f'--lora_r=4 '
               f'--lora_alpha=4 '
               f'--lora_bias=none '
               f'--lora_dropout=0.0 '
               f'--lora_text_encoder_r=4 '
               f'--lora_text_encoder_alpha=4 '
               f'--lora_text_encoder_bias=none '
               f'--lora_text_encoder_dropout=0.0 '
               f'--gradient_checkpointing '
               f'--resolution=512 '
               f'--train_batch_size=1 '
               f'--use_8bit_adam '
               f'--mixed_precision="fp16" '
               f'--gradient_accumulation_steps=1 '
               f'--learning_rate=1e-4 '
               f'--lr_scheduler="constant" '
               f'--lr_warmup_steps=0 '
               f'--max_train_steps=400')

    subprocess.run(cmd_str, shell=True)
    #bin_to_safetensors('/gcs/' + args.output_storage)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, default="runwayml/stable-diffusion-v1-5", help="bucket_name/model_folder")
    parser.add_argument("--input_storage", type=str,default="abc", help="bucket_name/input_image_folder")
    parser.add_argument("--output_storage", type=str, default="abc",help="bucket_name/output_folder")
    parser.add_argument("--prompt", type=str, default="abc",help="instance prompt")
    parser.add_argument("--class_prompt", type=str, default="abc",help="instance prompt")
    
    args = parser.parse_args()
    print(args.model_name)
    print(args.input_storage)
    print(args.output_storage)
    print(args.prompt)
    print(args.class_prompt)
    main(args)
