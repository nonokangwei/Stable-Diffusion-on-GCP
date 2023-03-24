# **Lora training using PEFT on Google Cloud Vertex AI**

This guide gives simple steps to fine tune Stable Diffusion using Lora based on PEFT library. The fine-tuning process will also be on Vertex AI.

* [Introduction](#Introduction)
* [Training on Vertex AI](#Training_on_Vertex_AI)
* [Workbench executor(WIP)](Workbench_executor)
* Model converted to safetensors(WIP)

## Introduction
   [PEFT](https://github.com/huggingface/peft) **Parameter-Efficient Fine-Tuning** methods enable efficient adaptation of pre-trained language models (PLMs) to various downstream applications without fine-tuning all the model's parameters. Supported methods:

- LoRA: LORA: LOW-RANK ADAPTATION OF LARGE LANGUAGE MODELS
- Prefix Tuning: Prefix-Tuning: Optimizing Continuous Prompts for Generation, P-Tuning v2: Prompt Tuning Can Be Comparable to Fine-tuning Universally Across Scales and Tasks
- P-Tuning: GPT Understands, Too
- Prompt Tuning: The Power of Scale for Parameter-Efficient Prompt Tuning

When training stable diffusion with LoRA, PEFT provides better implementation compared with Diffusers. The dreambooth_LoRA script provides more input arguments, including enabling text encoder training, configure lora_rank and so on, which can make users fine-tune the model more flexibly and more carefully.


In the project, we just use PEFT library, demo **Dreambooth with LoRA** training on GPU on Vertex AI. So the process is very similar with the Diffusers demo. We just skip some of the steps and only keep the key files (Dockerfile, train file, etc.) here. 

## Training on Vertex AI

1. Training

The code is in *CustomTraining* folder.

```
# Build the docker image
gcloud builds submit --config cloud-build-config.yaml .

# Submit training job
gcloud ai custom-jobs create \
  --region=us-central1 \
  --display-name=sd-lora-training-peft \
  --config=vertex-ai-config.yaml \
  --args="--model_name=runwayml/stable-diffusion-v1-5,--input_storage=/gcs/input_dog,--output_storage=sd_lsj/dog_lora_output,--prompt=a photo of sks dog"
```

2. Inference locally

The *inference.py* file implements inference library. It's referenced from [this repo](https://huggingface.co/spaces/smangrul/peft-lora-sd-dreambooth/tree/main). 
In *test.py*, we just load the inference library, and do the image generation work.

The generated LoRA model will have two files, one is *.pt file*, the other is *.json file*, both the files are named with prompt as prefix. So just pass the path of .pt file when inferencing, the .json file will be automatically routined.

## Workbench executor(WIP)

The code is in *Workbench* folder

```
# Build the docker image, configure the yaml file before running

gcloud builds submit --config cloud-build-workbench.yaml .
```

Then you can execute the notebook with custom built container. The model will be saved to Cloud Storage. And a test image will also be saved there.




