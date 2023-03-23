#!/bin/bash

echo "$@"
accelerate launch train_dreambooth_cust.py "$@"