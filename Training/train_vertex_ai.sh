#!/bin/bash

gcloud ai custom-jobs create \
  --region=us-central1 \
  --display-name=sd-dreambooth-training-mydog \
  --config=vertex_ai_config.yaml \
  --args="--pretrained_model_name_or_path=gs://hzchen-iowa/sd-models/realisticVisionV13.LtFu.safetensors,--instance_data_dir=gs://hzchen-iowa/dataset/alvan-nee-cropped,--with_prior_preservation,--prior_loss_weight=1.0,--class_data_dir=./class_dog,--output_dir=gs://hzchen-iowa/sd-models/mydog_real,--instance_prompt='a photo of my dog',--class_prompt='a photo of a dog',--resolution=512,--auto_guess"