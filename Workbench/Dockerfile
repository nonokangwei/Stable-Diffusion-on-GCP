FROM gcr.io/deeplearning-platform-release/base-gpu

RUN apt update
WORKDIR /root

RUN git clone -b v0.14.0 https://github.com/huggingface/diffusers.git \
  && pip install /root/diffusers \
  && pip install -U -r /root/diffusers/examples/dreambooth/requirements.txt \
  && pip install -U -r /root/diffusers/examples/text_to_image/requirements.txt \
  && pip install -U xformers \
  && pip install -U bitsandbytes --prefer-binary \
  && pip install -U safetensors

RUN pip install torch==1.13.1+cu117 torchvision==0.14.1+cu117 --extra-index-url https://download.pytorch.org/whl/cu117

ENV LD_LIBRARY_PATH $LD_LIBRARY_PATH:/usr/local/cuda/lib64
RUN ln -sf /usr/local/cuda/lib64/libcudart.so.11.0 /usr/local/cuda/lib64/libcudart.so

RUN accelerate config default --mixed_precision=fp16
