FROM python:3.10-bullseye

RUN curl -LO https://dl.k8s.io/release/v1.26.1/bin/linux/amd64/kubectl && \
    (echo d57be22cfa25f7427cfb538cfc8853d763878f8b36c76ce93830f6f2d67c6e5d kubectl|sha256sum -c ) && \
    install -m 755 kubectl /usr/bin/

WORKDIR /app
RUN curl -LO "https://dl.k8s.io/release/v1.27.1/bin/linux/amd64/kubectl" \
  && (echo 7fe3a762d926fb068bae32c399880e946e8caf3d903078bea9b169dcd5c17f6d kubectl|sha256sum -c)

COPY ./requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt

COPY ./* /app/

CMD /app/run.sh
