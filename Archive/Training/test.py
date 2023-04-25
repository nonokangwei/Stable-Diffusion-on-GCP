import os

os.system("cp -rp mydog_real/vae mydog_real/checkpoint-400")
os.system("python convert_diffusers_to_original_stable_diffusion.py --model_path=mydog_real/checkpoint-400 --checkpoint_path=./model_output/mydog_real-400.safetensors --use_safetensors")