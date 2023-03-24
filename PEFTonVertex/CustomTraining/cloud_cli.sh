# cloud build image
gcloud builds submit --config cloud-build-config.yaml .

# create vertex ai customer training job
# args format:
# --model_name: Huggingface repo id, or "/gcs/bucket_name/model_folder". I only test the models downloaded from HF, with standard diffusers format. Safetensors has not been test.
# --input_storage: bucket_name/input_image_folder
# --output_storage: bucket_name/output_folder
# --prompt: a photo of XXX
gcloud ai custom-jobs create \
  --region=us-central1 \
  --display-name=sd-lora-training-peft-1 \
  --config=vertex-ai-config.yaml \
  --args="--model_name=runwayml/stable-diffusion-v1-5,--input_storage=/gcs/sd_lsj/input_dog,--output_storage=/gcs/sd_lsj/peft/dog_lora_output,--prompt=a photo of sks dog,--class_prompt=a photo of dog"