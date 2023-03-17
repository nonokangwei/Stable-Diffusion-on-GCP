from glob import glob
import argparse

import os
os.getcwd()

# TODO
# 1. adjust arguments according to available VRAM
# 2. adjust arguments according to instance images number/person/object training
# 3. adjust arguments according to input folder/file type

MODELS_DIR = '/mnt/vol1/models/Stable-diffusion/'


def parse_args(input_args=None):
    parser = argparse.ArgumentParser(description="Simple example of a training script.")
    parser.add_argument(
        "--pretrained_model_name_or_path",
        type=str,
        default=None,
        required=True,
        help="Path to pretrained model or model identifier from huggingface.co/models.",
    )
    parser.add_argument(
        "--revision",
        type=str,
        default=None,
        required=False,
        help=(
            "Revision of pretrained model identifier from huggingface.co/models. Trainable model components should be"
            " float32 precision."
        ),
    )
    parser.add_argument(
        "--tokenizer_name",
        type=str,
        default=None,
        help="Pretrained tokenizer name or path if not the same as model_name",
    )
    parser.add_argument(
        "--instance_data_dir",
        type=str,
        default=None,
        required=True,
        help="A folder containing the training data of instance images.",
    )
    parser.add_argument(
        "--class_data_dir",
        type=str,
        default=None,
        required=False,
        help="A folder containing the training data of class images.",
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
        "--with_prior_preservation",
        default=False,
        action="store_true",
        help="Flag to add prior preservation loss.",
    )
    parser.add_argument("--prior_loss_weight", type=float, default=1.0, help="The weight of prior preservation loss.")
    parser.add_argument(
        "--num_class_images",
        type=int,
        default=100,
        help=(
            "Minimal class images for prior preservation loss. If there are not enough images already present in"
            " class_data_dir, additional images will be sampled with class_prompt."
        ),
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="text-inversion-model",
        help="The output directory where the model predictions and checkpoints will be written.",
    )
    parser.add_argument("--seed", type=int, default=None, help="A seed for reproducible training.")
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
        "--center_crop",
        default=False,
        action="store_true",
        help=(
            "Whether to center crop the input images to the resolution. If not set, the images will be randomly"
            " cropped. The images will be resized to the resolution first before cropping."
        ),
    )
    parser.add_argument(
        "--train_text_encoder",
        action="store_true",
        help="Whether to train the text encoder. If set, the text encoder should be float32 precision.",
    )
    parser.add_argument(
        "--train_batch_size", type=int, default=4, help="Batch size (per device) for the training dataloader."
    )
    parser.add_argument(
        "--sample_batch_size", type=int, default=4, help="Batch size (per device) for sampling images."
    )
    parser.add_argument("--num_train_epochs", type=int, default=1)
    parser.add_argument(
        "--max_train_steps",
        type=int,
        default=None,
        help="Total number of training steps to perform.  If provided, overrides num_train_epochs.",
    )
    parser.add_argument(
        "--checkpointing_steps",
        type=int,
        default=500,
        help=(
            "Save a checkpoint of the training state every X updates. Checkpoints can be used for resuming training via `--resume_from_checkpoint`. "
            "In the case that the checkpoint is better than the final trained model, the checkpoint can also be used for inference."
            "Using a checkpoint for inference requires separate loading of the original pipeline and the individual checkpointed model components."
            "See https://huggingface.co/docs/diffusers/main/en/training/dreambooth#performing-inference-using-a-saved-checkpoint for step by step"
            "instructions."
        ),
    )
    parser.add_argument(
        "--checkpoints_total_limit",
        type=int,
        default=None,
        help=(
            "Max number of checkpoints to store. Passed as `total_limit` to the `Accelerator` `ProjectConfiguration`."
            " See Accelerator::save_state https://huggingface.co/docs/accelerate/package_reference/accelerator#accelerate.Accelerator.save_state"
            " for more details"
        ),
    )
    parser.add_argument(
        "--resume_from_checkpoint",
        type=str,
        default=None,
        help=(
            "Whether training should be resumed from a previous checkpoint. Use a path saved by"
            ' `--checkpointing_steps`, or `"latest"` to automatically select the last available checkpoint.'
        ),
    )
    parser.add_argument(
        "--gradient_accumulation_steps",
        type=int,
        default=1,
        help="Number of updates steps to accumulate before performing a backward/update pass.",
    )
    parser.add_argument(
        "--gradient_checkpointing",
        action="store_true",
        help="Whether or not to use gradient checkpointing to save memory at the expense of slower backward pass.",
    )
    parser.add_argument(
        "--learning_rate",
        type=float,
        default=5e-6,
        help="Initial learning rate (after the potential warmup period) to use.",
    )
    parser.add_argument(
        "--scale_lr",
        action="store_true",
        default=False,
        help="Scale the learning rate by the number of GPUs, gradient accumulation steps, and batch size.",
    )
    parser.add_argument(
        "--lr_scheduler",
        type=str,
        default="constant",
        help=(
            'The scheduler type to use. Choose between ["linear", "cosine", "cosine_with_restarts", "polynomial",'
            ' "constant", "constant_with_warmup"]'
        ),
    )
    parser.add_argument(
        "--lr_warmup_steps", type=int, default=500, help="Number of steps for the warmup in the lr scheduler."
    )
    parser.add_argument(
        "--lr_num_cycles",
        type=int,
        default=1,
        help="Number of hard resets of the lr in cosine_with_restarts scheduler.",
    )
    parser.add_argument("--lr_power", type=float, default=1.0, help="Power factor of the polynomial scheduler.")
    parser.add_argument(
        "--use_8bit_adam", action="store_true", help="Whether or not to use 8-bit Adam from bitsandbytes."
    )
    parser.add_argument(
        "--dataloader_num_workers",
        type=int,
        default=0,
        help=(
            "Number of subprocesses to use for data loading. 0 means that the data will be loaded in the main process."
        ),
    )
    parser.add_argument("--adam_beta1", type=float, default=0.9, help="The beta1 parameter for the Adam optimizer.")
    parser.add_argument("--adam_beta2", type=float, default=0.999, help="The beta2 parameter for the Adam optimizer.")
    parser.add_argument("--adam_weight_decay", type=float, default=1e-2, help="Weight decay to use.")
    parser.add_argument("--adam_epsilon", type=float, default=1e-08, help="Epsilon value for the Adam optimizer")
    parser.add_argument("--max_grad_norm", default=1.0, type=float, help="Max gradient norm.")
    parser.add_argument("--push_to_hub", action="store_true", help="Whether or not to push the model to the Hub.")
    parser.add_argument("--hub_token", type=str, default=None, help="The token to use to push to the Model Hub.")
    parser.add_argument(
        "--hub_model_id",
        type=str,
        default=None,
        help="The name of the repository to keep in sync with the local `output_dir`.",
    )
    parser.add_argument(
        "--logging_dir",
        type=str,
        default="logs",
        help=(
            "[TensorBoard](https://www.tensorflow.org/tensorboard) log directory. Will default to"
            " *output_dir/runs/**CURRENT_DATETIME_HOSTNAME***."
        ),
    )
    parser.add_argument(
        "--allow_tf32",
        action="store_true",
        help=(
            "Whether or not to allow TF32 on Ampere GPUs. Can be used to speed up training. For more information, see"
            " https://pytorch.org/docs/stable/notes/cuda.html#tensorfloat-32-tf32-on-ampere-devices"
        ),
    )
    parser.add_argument(
        "--report_to",
        type=str,
        default="tensorboard",
        help=(
            'The integration to report the results and logs to. Supported platforms are `"tensorboard"`'
            ' (default), `"wandb"` and `"comet_ml"`. Use `"all"` to report to all integrations.'
        ),
    )
    parser.add_argument(
        "--validation_prompt",
        type=str,
        default=None,
        help="A prompt that is used during validation to verify that the model is learning.",
    )
    parser.add_argument(
        "--num_validation_images",
        type=int,
        default=4,
        help="Number of images that should be generated during validation with `validation_prompt`.",
    )
    parser.add_argument(
        "--validation_steps",
        type=int,
        default=100,
        help=(
            "Run validation every X steps. Validation consists of running the prompt"
            " `args.validation_prompt` multiple times: `args.num_validation_images`"
            " and logging the images."
        ),
    )
    parser.add_argument(
        "--mixed_precision",
        type=str,
        default=None,
        choices=["no", "fp16", "bf16"],
        help=(
            "Whether to use mixed precision. Choose between fp16 and bf16 (bfloat16). Bf16 requires PyTorch >="
            " 1.10.and an Nvidia Ampere GPU.  Default to the value of accelerate config of the current system or the"
            " flag passed with the `accelerate.launch` command. Use this argument to override the accelerate config."
        ),
    )
    parser.add_argument(
        "--prior_generation_precision",
        type=str,
        default=None,
        choices=["no", "fp32", "fp16", "bf16"],
        help=(
            "Choose prior generation precision between fp32, fp16 and bf16 (bfloat16). Bf16 requires PyTorch >="
            " 1.10.and an Nvidia Ampere GPU.  Default to  fp16 if a GPU is available else fp32."
        ),
    )
    parser.add_argument("--local_rank", type=int, default=-1, help="For distributed training: local_rank")
    parser.add_argument(
        "--enable_xformers_memory_efficient_attention", action="store_true", help="Whether or not to use xformers."
    )
    parser.add_argument(
        "--set_grads_to_none",
        action="store_true",
        help=(
            "Save more memory by using setting grads to None instead of zero. Be aware, that this changes certain"
            " behaviors, so disable this argument if it causes any problems. More info:"
            " https://pytorch.org/docs/stable/generated/torch.optim.Optimizer.zero_grad.html"
        ),
    )
    #
    parser.add_argument(
        "--auto_guess",
        action="store_true",
        help=(
            "Auto guess the best parameters according to input image numbers, available vram, and more"
        ),
    )

    if input_args is not None:
        args = parser.parse_args(input_args)
    else:
        args = parser.parse_args()

    env_local_rank = int(os.environ.get("LOCAL_RANK", -1))
    if env_local_rank != -1 and env_local_rank != args.local_rank:
        args.local_rank = env_local_rank

    if args.with_prior_preservation:
        if args.class_data_dir is None:
            raise ValueError("You must specify a data directory for class images.")
        if args.class_prompt is None:
            raise ValueError("You must specify prompt for class images.")
    else:
        # logger is not available yet
        if args.class_data_dir is not None:
            warnings.warn("You need not use --class_data_dir without --with_prior_preservation.")
        if args.class_prompt is not None:
            warnings.warn("You need not use --class_prompt without --with_prior_preservation.")

    return args


from diffusers.pipelines.stable_diffusion.convert_from_ckpt import download_from_original_stable_diffusion_ckpt

sd_to_diff_parser = argparse.ArgumentParser()

sd_to_diff_parser.add_argument(
    "--checkpoint_path", default=None, type=str, required=True, help="Path to the checkpoint to convert."
)
# !wget https://raw.githubusercontent.com/CompVis/stable-diffusion/main/configs/stable-diffusion/v1-inference.yaml
sd_to_diff_parser.add_argument(
    "--original_config_file",
    default=None,
    type=str,
    help="The YAML config file corresponding to the original architecture.",
)
sd_to_diff_parser.add_argument(
    "--num_in_channels",
    default=None,
    type=int,
    help="The number of input channels. If `None` number of input channels will be automatically inferred.",
)
sd_to_diff_parser.add_argument(
    "--scheduler_type",
    default="pndm",
    type=str,
    help="Type of scheduler to use. Should be one of ['pndm', 'lms', 'ddim', 'euler', 'euler-ancestral', 'dpm']",
)
sd_to_diff_parser.add_argument(
    "--pipeline_type",
    default=None,
    type=str,
    help=(
        "The pipeline type. One of 'FrozenOpenCLIPEmbedder', 'FrozenCLIPEmbedder', 'PaintByExample'"
        ". If `None` pipeline will be automatically inferred."
    ),
)
sd_to_diff_parser.add_argument(
    "--image_size",
    default=None,
    type=int,
    help=(
        "The image size that the model was trained on. Use 512 for Stable Diffusion v1.X and Stable Siffusion v2"
        " Base. Use 768 for Stable Diffusion v2."
    ),
)
sd_to_diff_parser.add_argument(
    "--prediction_type",
    default=None,
    type=str,
    help=(
        "The prediction type that the model was trained on. Use 'epsilon' for Stable Diffusion v1.X and Stable"
        " Diffusion v2 Base. Use 'v_prediction' for Stable Diffusion v2."
    ),
)
sd_to_diff_parser.add_argument(
    "--extract_ema",
    action="store_true",
    help=(
        "Only relevant for checkpoints that have both EMA and non-EMA weights. Whether to extract the EMA weights"
        " or not. Defaults to `False`. Add `--extract_ema` to extract the EMA weights. EMA weights usually yield"
        " higher quality images for inference. Non-EMA weights are usually better to continue fine-tuning."
    ),
)
sd_to_diff_parser.add_argument(
    "--upcast_attention",
    action="store_true",
    help=(
        "Whether the attention computation should always be upcasted. This is necessary when running stable"
        " diffusion 2.1."
    ),
)
sd_to_diff_parser.add_argument(
    "--from_safetensors",
    action="store_true",
    help="If `--checkpoint_path` is in `safetensors` format, load checkpoint with safetensors instead of PyTorch.",
)
sd_to_diff_parser.add_argument(
    "--to_safetensors",
    action="store_true",
    help="Whether to store pipeline in safetensors format or not.",
)
sd_to_diff_parser.add_argument("--dump_path", default=None, type=str, required=True, help="Path to the output model.")
sd_to_diff_parser.add_argument("--device", type=str, help="Device to use (e.g. cpu, cuda:0, cuda:1, etc.)")
sd_to_diff_parser.add_argument(
    "--stable_unclip",
    type=str,
    default=None,
    required=False,
    help="Set if this is a stable unCLIP model. One of 'txt2img' or 'img2img'.",
)
sd_to_diff_parser.add_argument(
    "--stable_unclip_prior",
    type=str,
    default=None,
    required=False,
    help="Set if this is a stable unCLIP txt2img model. Selects which prior to use. If `--stable_unclip` is set to `txt2img`, the karlo prior (https://huggingface.co/kakaobrain/karlo-v1-alpha/tree/main/prior) is selected by default.",
)
sd_to_diff_parser.add_argument(
    "--clip_stats_path",
    type=str,
    help="Path to the clip stats file. Only required if the stable unclip model's config specifies `model.params.noise_aug_config.params.clip_stats_path`.",
    required=False,
)
sd_to_diff_parser.add_argument(
    "--controlnet", action="store_true", default=None, help="Set flag if this is a controlnet checkpoint."
)


args = parse_args()

basename = None
if os.path.isfile(args.pretrained_model_name_or_path):
    file = args.pretrained_model_name_or_path
    basename = file.split('/')[-1].split('.')[0]
    file_extension = file.split('/')[-1].split('.')[-1]


if basename:
    sd_to_diff_parser_input_args = [
        '--checkpoint_path={}'.format(args.pretrained_model_name_or_path),
        '--dump_path={}'.format(basename),
    ]
    if file_extension == 'safetensors':
        sd_to_diff_parser_input_args.append('--from_safetensors')
    if args.resolution:
        sd_to_diff_parser_input_args.append('--image_size={}'.format(args.resolution))
    if os.path.isfile(basename + '.yaml'):
        sd_to_diff_parser_input_args.append('--original_config_file={}'.format(basename + '.yaml'))
        
    sd_to_diff_args = sd_to_diff_parser.parse_args(sd_to_diff_parser_input_args)
    
    pipe = download_from_original_stable_diffusion_ckpt(
        checkpoint_path=sd_to_diff_args.checkpoint_path,
        original_config_file=sd_to_diff_args.original_config_file,
        image_size=sd_to_diff_args.image_size,
        prediction_type=sd_to_diff_args.prediction_type,
        model_type=sd_to_diff_args.pipeline_type,
        extract_ema=sd_to_diff_args.extract_ema,
        scheduler_type=sd_to_diff_args.scheduler_type,
        num_in_channels=sd_to_diff_args.num_in_channels,
        upcast_attention=sd_to_diff_args.upcast_attention,
        from_safetensors=sd_to_diff_args.from_safetensors,
        device=sd_to_diff_args.device,
        stable_unclip=sd_to_diff_args.stable_unclip,
        stable_unclip_prior=sd_to_diff_args.stable_unclip_prior,
        clip_stats_path=sd_to_diff_args.clip_stats_path,
        controlnet=sd_to_diff_args.controlnet,
    )

    if sd_to_diff_args.controlnet:
        # only save the controlnet model
        pipe.controlnet.save_pretrained(sd_to_diff_args.dump_path, safe_serialization=sd_to_diff_args.to_safetensors)
    else:
        pipe.save_pretrained(sd_to_diff_args.dump_path, safe_serialization=sd_to_diff_args.to_safetensors)

    args.pretrained_model_name_or_path = sd_to_diff_args.dump_path

import nvidia_smi

nvidia_smi.nvmlInit()

handle = nvidia_smi.nvmlDeviceGetHandleByIndex(0)
# card id 0 hardcoded here, there is also a call to get all available card ids, so we could iterate

gpu_info = nvidia_smi.nvmlDeviceGetMemoryInfo(handle)

print("Total memory:", gpu_info.total/1024/1024/1024)
print("Free memory:", gpu_info.free/1024/1024/1024)
print("Used memory:", gpu_info.used/1024/1024/1024)

nvidia_smi.nvmlShutdown()

if args.auto_guess:
    args.with_prior_preservation = True
    args.prior_loss_weight = 1.0
    args.train_text_encoder = True
    args.learning_rate = 1e-06
    args.lr_scheduler = "polynomial"
    num_instance_images = len(glob(os.path.join(args.instance_data_dir, '*')))
    args.num_class_images = num_instance_images * 12
    args.max_train_steps = min(int(num_instance_images * 80 * 1.25), 1500)
    args.lr_warmup_steps = args.max_train_steps // 10
    args.checkpoints_total_limit = 5
    args.checkpointing_steps = args.max_train_steps // args.checkpoints_total_limit
    args.mixed_precision = "fp16"
    args.use_8bit_adam = True
    args.train_batch_size = 1
    args.enable_xformers_memory_efficient_attention = True
    if gpu_info.free >= 24*1024*1024*1024:
        args.gradient_checkpointing = False
        args.train_batch_size = 2
        # args.train_text_encoder = True
    else:
        args.gradient_accumulation_steps = 1
        args.gradient_checkpointing = True
        # args.train_text_encoder = False

print("DEBUG: ", args.gradient_checkpointing, args.train_text_encoder, args.train_batch_size, gpu_info.free)

from train_dreambooth import main
main(args)

checkpoint_dirs = glob(os.path.join(args.output_dir, 'checkpoint-*'))
for dir in checkpoint_dirs:
    os.system("cp -rp {}/vae {}".format(args.output_dir, dir))
    os.system("python convert_diffusers_to_original_stable_diffusion.py --model_path={} --checkpoint_path={} --use_safetensors".format(dir, os.path.join(MODELS_DIR, args.output_dir + '.safetensors')))

