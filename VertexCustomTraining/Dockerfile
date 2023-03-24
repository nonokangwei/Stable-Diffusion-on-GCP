FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

RUN apt update
RUN apt install -y wget git python3 python3-venv python3-pip

RUN pip install torch==1.13.1+cu117 torchvision==0.14.1+cu117 --extra-index-url https://download.pytorch.org/whl/cu117

WORKDIR /root

RUN git clone -b v0.14.0 https://github.com/huggingface/diffusers.git \
  && pip install /root/diffusers \
  && pip install -U -r /root/diffusers/examples/dreambooth/requirements.txt \
  && pip install -U -r /root/diffusers/examples/text_to_image/requirements.txt \
  && pip install -U xformers \ 
  && pip install -U safetensors

# Solve Bitbytes and CUDA conflict issue
ENV LD_LIBRARY_PATH $LD_LIBRARY_PATH:/usr/local/cuda/lib64
RUN ln -s /usr/local/cuda/lib64/libcudart.so.11.0 /usr/local/cuda/lib64/libcudart.so
RUN pip install -U bitsandbytes --prefer-binary

# Config accelerate
RUN accelerate config default --mixed_precision=fp16

# Installs additional packages as you need.
RUN pip install google-cloud-aiplatform
RUN pip install google-cloud-storage

# Copies the trainer code to the docker image.
COPY train.py /root/train.py

# Sets up the entry point to invoke the trainer.
ENTRYPOINT ["python3", "-m", "train"]