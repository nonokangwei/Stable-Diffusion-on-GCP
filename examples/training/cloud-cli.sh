# cloud build image
gcloud builds submit --config cloud-build-config-kohya.yaml .

# create vertex ai customer training job
# args format:
# --model_name: Huggingface repo id, or "/gcs/bucket_name/model_folder". I only test the models downloaded from HF, with standard diffusers format. Safetensors has not been test.
# --input_storage: /gcs/bucket_name/input_image_folder
#     images put in subfolder, with foder name repeat num per image_prompt name, eg. 10_aki
#     you can also put caption.txt file in the folder.
# --output_storage: /gcs/bucket_name/output_folder
# --display_name: prompt name
# input_storage, output_storage, and display_name are required, other arguments are optional.
# --resolution='512,512'
gcloud ai custom-jobs create  \
  --region=us-central1 \
  --display-name=sd-kohya-test02  \
  --config=vertex_t4_config_nfs.yaml   \
  --args="launch,--num_cpu_threads_per_process=2,train_network.py,--enable_bucket,--pretrained_model_name_or_path=runwayml/stable-diffusion-v1-5,--resolution=512,--train_data_dir=/mnt/nfs/working_dir/img/,--output_dir=/mnt/nfs/working_dir/output,--network_alpha=1,--save_model_as=safetensors,--network_module=networks.lora,--text_encoder_lr=5e-05,--unet_lr=0.0001,--network_dim=8,--output_name=last,--lr_scheduler_num_cycles=1,--learning_rate=0.0001,--lr_scheduler=cosine,--lr_warmup_steps=0,--train_batch_size=1,--max_train_steps=610,--mixed_precision=fp16,--save_precision=fp16,--cache_latents,--optimizer_type=AdamW8bit,--max_data_loader_n_workers=0,--bucket_reso_steps=64,--xformers,--bucket_no_upscale" \
  --command="python3,/usr/local/bin/accelerate"

# Debug
gcloud ai custom-jobs create  \
  --region=us-central1   \
  --display-name=sd-kohya-debug  \
  --config=vertex_t4_config_nfs.yaml   \
  --args="" \
  --command="bash,/kohya_ss/debug.sh"

# only save the models in GCS to Filestore
# gcloud ai custom-jobs create  \
#   --region=us-central1   \
#   --display-name=sd-kohya   \
#   --config=vertex-config-nfs.yaml   \
#   --args="--output_storage=/gcs/sd_lsj/kohya_output,--save_nfs_only=True" \
#   --command="python3,train_kohya.py"