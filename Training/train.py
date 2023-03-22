import subprocess
import os
import argparse
from pprint import pprint

# train_dreambooth_cust.py \
#   --pretrained_model_name_or_path=./realisticVisionV13.LtFu.safetensors \
#   --instance_data_dir=/mnt/vol1/inputs/alvan-nee-cropped \
#   --with_prior_preservation --prior_loss_weight=1.0 \
#   --class_data_dir=./class_dog --output_dir=./mydog_real \
#   --instance_prompt="a photo of my dog" --class_prompt="a photo of a dog" \
#   --resolution=512 --models_dir=/mnt/vol1/models/Stable-diffusion/mydog_real/ \
#   --auto_guess

# python train.py \
#     --auto_guess \
#     --pretrained_model_name_or_path=./realisticVisionV13.LtFu.safetensors \
#     --instance_data_dir=/mnt/vol1/inputs/alvan-nee-cropped \
#     --output_name="mydog_real" \
#     --instance_prompt="photo of my dog" \
#     --class_prompt="photo of a dog" \
#     --resolution=512
    
    
def main(args):
    #subprocess.run("accelerate config update --config_file /content/accelerate_2.yaml", shell=True)
    # os.chdir("/root/")

    # for complex commands, with many args, use string + `shell=True`:
    cmd_str = (f'accelerate launch train_dreambooth_cust.py '
               f'--pretrained_model_name_or_path={args.pretrained_model_name_or_path} '
               f'--instance_data_dir={args.instance_data_dir} '
               f'--output_dir="{args.output_name}" '
               f'--instance_prompt="{args.instance_prompt}" '
               f'--class_prompt="{args.class_prompt}" '
               f'--class_data_dir=./class_dir '
               f'--resolution={args.resolution} '
               f'--models_dir=./model_output '
               f'--auto_guess')

    print(cmd_str)
    subprocess.run(cmd_str, shell=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--auto_guess",
        action="store_true",
        help=(
            "Auto guess the best parameters according to input image numbers, available vram, and more"
        ),
    )
    parser.add_argument(
        "--pretrained_model_name_or_path",
        type=str,
        default=None,
        required=True,
        help="Path to pretrained model or model identifier from huggingface.co/models.",
    )
    parser.add_argument(
        "--output_name",
        type=str,
        default=None,
        required=True,
        help="Name of the new model, would be used as part of the model file name",
    )
    parser.add_argument(
        "--instance_data_dir",
        type=str,
        default=None,
        required=True,
        help="A folder containing the training data of instance images.",
    )
    parser.add_argument(
        "--instance_prompt",
        type=str,
        default=None,
        required=True,
        help="The prompt with identifier specifying the instance",
    )
    parser.add_argument(
        "--class_prompt",
        type=str,
        default=None,
        help="The prompt to specify images in the same class as provided instance images.",
    )
    parser.add_argument(
        "--resolution",
        type=int,
        default=512,
        help=(
            "The resolution for input images, all the images in the train/validation dataset will be resized to this"
            " resolution"
        ),
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=None,
        required=True,
        help="Path to store output models, support gcs and local path",
    )


    args = parser.parse_args()
    pprint(vars(args))
    main(args)

    if str(args.output_dir).startswith('gs://'):
        subprocess.run("gcloud storage cp -r {} {}".format(os.path.join('./model_output', '*'), args.output_dir), shell=True)
    else:
        subprocess.run("cp -r {} {}".format(os.path.join('./model_output', '*'), args.output_dir), shell=True)
