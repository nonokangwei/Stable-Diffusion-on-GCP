# cloud build image
gcloud builds submit --config cloud-build-config.yaml .

# create vertex ai customer training job
# args format:
# --model_name: Huggingface repo id, or "/gcs/bucket_name/model_folder". I only test the models downloaded from HF, with standard diffusers format. Safetensors has not been test.
# --input_storage: /gcs/bucket_name/input_image_folder
#     for dreambooth: just put images in the image folder
#     for text-to-image: put images and metadata.jsonl in the image folder
# --output_storage: /gcs/bucket_name/output_folder
# --prompt: a photo of XXX
# --set_grads_to_none: for training dreambooth on T4
gcloud ai custom-jobs create \
  --region=us-central1 \
  --display-name=sd-diffuser-t2i-1v100 \
  --config=vertex-config-1v100.yaml \
  --args="--method=diffuser_text_to_image,--model_name=CompVis/stable-diffusion-v1-4,--input_storage=/gcs/sd_lsj/input_dog_t2i,--output_storage=/gcs/sd_lsj/diffusers_t2i_output,--resolution=512,--batch_size=1,--lr=1e-4,--use_8bit=True,--max_train_steps=100"
  --command="python3,train.py"
