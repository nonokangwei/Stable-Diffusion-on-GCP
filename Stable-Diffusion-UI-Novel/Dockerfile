FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

RUN apt update

RUN apt install -y wget git python3 python3-venv python3-pip

RUN git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git

RUN cd stable-diffusion-webui \
    && git -C . checkout 828438b4a190759807f9054932cae3a8b880ddf1

COPY model.ckpt /stable-diffusion-webui/models/Stable-diffusion/

RUN pip install torch==1.12.1+cu113 torchvision==0.13.1+cu113 --extra-index-url https://download.pytorch.org/whl/cu113 

RUN set -ex && cd stable-diffusion-webui \
    && mkdir repositories \
    && git clone https://github.com/CompVis/stable-diffusion.git repositories/stable-diffusion \
    && git clone https://github.com/CompVis/taming-transformers.git repositories/taming-transformers\
    && git clone https://github.com/sczhou/CodeFormer.git repositories/CodeFormer \
    && git clone https://github.com/salesforce/BLIP.git repositories/BLIP \
    && git clone https://github.com/crowsonkb/k-diffusion.git repositories/k-diffusion \
    && pip install transformers==4.19.2 diffusers invisible-watermark --prefer-binary \
    && pip install git+https://github.com/crowsonkb/k-diffusion.git --prefer-binary \
    && pip install git+https://github.com/TencentARC/GFPGAN.git --prefer-binary \
    && pip install -r repositories/CodeFormer/requirements.txt --prefer-binary \
    && pip install -r requirements.txt  --prefer-binary \
    && pip install -U numpy  --prefer-binary

RUN pip install opencv-contrib-python-headless opencv-python-headless

EXPOSE 7860

CMD ["python3", "/stable-diffusion-webui/webui.py", "--listen"]