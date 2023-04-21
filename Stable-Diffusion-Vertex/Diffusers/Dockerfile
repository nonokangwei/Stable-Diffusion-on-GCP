FROM gcr.io/deeplearning-platform-release/base-gpu.py310

RUN apt-get update

WORKDIR /root

#install sd libraries
RUN git clone -b v0.14.0 https://github.com/huggingface/diffusers.git
RUN pip install /root/diffusers
RUN git clone https://github.com/huggingface/peft.git
RUN pip install /root/peft 
RUN git clone https://huggingface.co/spaces/smangrul/peft-lora-sd-dreambooth

#install libraries
#RUN pip install -U xformers safetensors tqdm ftfy loralib evaluate psutil pyyaml packaging bitsandbytes==0.35.0 datasets
RUN pip install xformers==0.0.18
RUN pip install safetensors==0.3.0
RUN pip install tqdm==4.65.0
RUN pip install ftfy==6.1.1
RUN pip install loralib==0.1.1
RUN pip install evaluate==0.4.0
RUN pip install psutil==5.9.4
RUN pip install pyYAML==6.0
RUN pip install packaging==21.3
RUN pip install datasets==2.11.0
RUN pip install bitsandbytes==0.35.0
RUN pip install transformers==4.27.4
RUN pip install accelerate==0.18.0
RUN pip install Jinja2==3.1.2

#install pytorch
RUN pip install torch==2.0.0+cu118 torchvision==0.15.1+cu118 --extra-index-url https://download.pytorch.org/whl/cu118

# Installs gcp libraries
RUN pip install google-cloud-aiplatform
RUN pip install google-cloud-storage

# Copies the trainer code to the docker image.
COPY train.py /root/train.py

# Sets up the entry point to invoke the trainer.
ENTRYPOINT ["python3", "-m", "train"]

