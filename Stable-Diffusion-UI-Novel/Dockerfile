FROM nvidia/cuda:12.0.1-runtime-ubuntu22.04

RUN set -ex && \
    apt update && \
    apt install -y wget git python3 python3-venv python3-pip

RUN git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git

RUN cd stable-diffusion-webui

COPY model.ckpt /stable-diffusion-webui/models/Stable-diffusion/

RUN pip install torch==1.13.1+cu117 torchvision==0.14.1+cu117 --extra-index-url https://download.pytorch.org/whl/cu117 

RUN set -ex && cd stable-diffusion-webui \
    && mkdir repositories \
    && git clone https://github.com/CompVis/stable-diffusion.git repositories/stable-diffusion \
    && git clone https://github.com/CompVis/taming-transformers.git repositories/taming-transformers\
    && git clone https://github.com/sczhou/CodeFormer.git repositories/CodeFormer \
    && git clone https://github.com/salesforce/BLIP.git repositories/BLIP \
    && git clone https://github.com/crowsonkb/k-diffusion.git repositories/k-diffusion \
    && git clone https://github.com/Stability-AI/stablediffusion repositories/stable-diffusion-stability-ai \
    && pip install transformers diffusers invisible-watermark --prefer-binary \
    && pip install git+https://github.com/crowsonkb/k-diffusion.git --prefer-binary \
    && pip install git+https://github.com/TencentARC/GFPGAN.git --prefer-binary \
    && pip install git+https://github.com/mlfoundations/open_clip.git@bb6e834e9c70d9c27d0dc3ecedeebeaeb1ffad6b --prefer-binary \
    && pip install -r repositories/CodeFormer/requirements.txt --prefer-binary \
    && pip install -r requirements.txt  --prefer-binary \
    && pip install -U "numpy<1.24"  --prefer-binary

RUN pip install opencv-contrib-python-headless opencv-python-headless
RUN pip install --upgrade fastapi==0.90.1

EXPOSE 7860

CMD ["python3", "/stable-diffusion-webui/webui.py", "--listen"]