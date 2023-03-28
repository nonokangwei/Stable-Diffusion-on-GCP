FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

WORKDIR /root

RUN apt update -y && \
    apt install -y wget git python3 python3-venv python3-pip curl \
    apt-transport-https ca-certificates gnupg libpng-dev libjpeg-dev && \
    rm -rf /var/lib/apt/lists/*

RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | \
  tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
  apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - && apt-get update -y && \
  apt-get install google-cloud-cli -y

RUN pip install torch==1.13.1+cu117 torchvision==0.14.1+cu117 --extra-index-url https://download.pytorch.org/whl/cu117

WORKDIR /root

# RUN git clone -b v0.14.0 https://github.com/huggingface/diffusers.git \
RUN git clone https://github.com/huggingface/diffusers.git \
  && pip install /root/diffusers \
  && pip install -U -r /root/diffusers/examples/dreambooth/requirements.txt --prefer-binary \
  && pip install -U -r /root/diffusers/examples/text_to_image/requirements.txt --prefer-binary \
  && pip install -U xformers safetensors omegaconf --prefer-binary

ENV LD_LIBRARY_PATH $LD_LIBRARY_PATH:/usr/local/cuda/lib64
RUN ln -s /usr/local/cuda/lib64/libcudart.so.11.0 /usr/local/cuda/lib64/libcudart.so
RUN pip install -U bitsandbytes --prefer-binary

# Installs additional packages as you need.
RUN pip install google-cloud-aiplatform
RUN pip install google-cloud-storage

# Copies the trainer code to the docker image.
COPY *.py /root/

# Sets up the entry point to invoke the trainer.
ENTRYPOINT ["python3", "-m", "train_db_entry"]