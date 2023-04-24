FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

RUN set -ex && \
    apt update && \
    apt install -y wget git python3 python3-venv python3-pip xdg-utils && \
    rm -rf /var/lib/apt/lists/*

ENV LD_LIBRARY_PATH $LD_LIBRARY_PATH:/usr/local/cuda/lib64
RUN ln -s /usr/local/cuda/lib64/libcudart.so.11.0 /usr/local/cuda/lib64/libcudart.so

RUN git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git

RUN set -ex && cd stable-diffusion-webui \
    && mkdir repositories \
    && git clone https://github.com/CompVis/stable-diffusion.git repositories/stable-diffusion \
    && git clone https://github.com/CompVis/taming-transformers.git repositories/taming-transformers\
    && git clone https://github.com/sczhou/CodeFormer.git repositories/CodeFormer \
    && git clone https://github.com/salesforce/BLIP.git repositories/BLIP \
    && git clone https://github.com/crowsonkb/k-diffusion.git repositories/k-diffusion \
    && git clone https://github.com/Stability-AI/stablediffusion repositories/stable-diffusion-stability-ai \
    && git clone https://github.com/Mikubill/sd-webui-controlnet.git extensions/sd-webui-controlnet \
    && git clone https://github.com/d8ahazard/sd_dreambooth_extension.git extensions/sd_dreambooth_extension \
    && pip install transformers diffusers invisible-watermark --prefer-binary \
    && pip install git+https://github.com/crowsonkb/k-diffusion.git --prefer-binary \
    && pip install git+https://github.com/TencentARC/GFPGAN.git --prefer-binary \
    && pip install git+https://github.com/mlfoundations/open_clip.git --prefer-binary \
    && pip install -r repositories/CodeFormer/requirements.txt --prefer-binary \
    && pip install -r requirements.txt --prefer-binary \
    && pip install -r extensions/sd_dreambooth_extension/requirements.txt --prefer-binary \
    && pip install -r extensions/sd-webui-controlnet/requirements.txt --prefer-binary

RUN pip install opencv-contrib-python-headless opencv-python-headless tensorrt --prefer-binary
RUN pip install -U --pre xformers torch==2.0.0+cu117 torchvision==0.15.1+cu117 --extra-index-url https://download.pytorch.org/whl/cu117 --prefer-binary
RUN pip install -U tensorboard google-auth-oauthlib tb-nightly open-clip-torch clean-fid --prefer-binary

ARG CUDNN_PATH=$(dirname $(python3 -c "import nvidia.cudnn;print(nvidia.cudnn.__file__)"))
ARG TENSORRT_PATH=$(dirname $(python3 -c "import tensorrt;print(tensorrt.__file__)"))
ENV LD_LIBRARY_PATH $LD_LIBRARY_PATH:/usr/local/cuda/lib64:$CUDNN_PATH:$TENSORRT_PATH

EXPOSE 7860

COPY user-watch.py /stable-diffusion-webui/user-watch.py
COPY start.sh /stable-diffusion-webui/start.sh

WORKDIR /stable-diffusion-webui/
CMD ["python3", "webui.py", "--listen", "--xformers",  "--enable-insecure-extension-access", "--no-gradio-queue"]