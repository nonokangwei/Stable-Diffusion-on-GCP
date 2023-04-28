# cloud build image
gcloud builds submit --config cloud-build-config-hpo.yaml .

#creat hp-tuning job
gcloud ai hp-tuning-jobs create  \
   --region=us-central1 \
   --display-name=sd-kohya-hpo \
   --max-trial-count=5 \
   --parallel-trial-count=2 \
   --config=vertex-config-hpo.yaml