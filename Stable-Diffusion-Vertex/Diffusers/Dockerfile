FROM gcr.io/deeplearning-platform-release/base-gpu.py310

RUN apt-get update

WORKDIR /root

#install sd libraries
RUN git clone -b v0.14.0 https://github.com/huggingface/diffusers.git
RUN pip install /root/diffusers
RUN git clone https://github.com/huggingface/peft.git
RUN pip install /root/peft 
RUN git clone https://huggingface.co/spaces/smangrul/peft-lora-sd-dreambooth

RUN pip install -U xformers safetensors tqdm ftfy loralib evaluate psutil pyyaml packaging bitsandbytes==0.35.0 datasets

#install pytorch
RUN pip install torch==2.0.0+cu118 torchvision==0.15.1+cu118 --extra-index-url https://download.pytorch.org/whl/cu118

# Installs gcp libraries
RUN pip install google-cloud-aiplatform
RUN pip install google-cloud-storage

# Copies the trainer code to the docker image.
COPY train.py /root/train.py

# Sets up the entry point to invoke the trainer.
#ENTRYPOINT ["python3", "-m", "train"]

