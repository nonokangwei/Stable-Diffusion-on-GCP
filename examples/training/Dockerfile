FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

RUN set -ex && \
    apt update && \
    apt install -y wget git python3 python3-venv python3-pip libglib2.0-0 pkg-config libcairo2-dev ffmpeg libsm6 libxext6 tree && \
    rm -rf /var/lib/apt/lists/*

ENV LD_LIBRARY_PATH=/usr/local/cuda/lib64:/usr/local/nvidia/lib:/usr/local/nvidia/lib64
RUN python3 -m pip install torch torchvision --prefer-binary
RUN python3 -m pip install xformers --prefer-binary
RUN git clone https://github.com/bmaltais/kohya_ss.git
RUN cd /kohya_ss/ && \
    python3 -m pip install -r /kohya_ss/requirements_unix.txt --prefer-binary
RUN python3 -m pip install -U bitsandbytes --prefer-binary

WORKDIR /kohya_ss/