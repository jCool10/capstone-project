# 1. Deploy VLLM

## 1.1. Setup GCP

SSH vào instance:
gcloud compute ssh vllm-llm-instance

Cài đặt Docker:
sudo apt update
sudo apt install -y docker.io
sudo usermod -aG docker $USER
newgrp docker

Cài đặt NVIDIA Driver và CUDA Toolkit:
Cài đặt driver NVIDIA
sudo apt install -y nvidia-driver-525-server

Reboot để nhận diện GPU
sudo reboot

Sau reboot, SSH lại vào VM:
gcloud compute ssh vllm-llm-instance

Cài đặt NVIDIA Container Toolkit:
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

Kiểm tra cài đặt GPU Docker:
docker run --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

docker run --gpus all --name my_vllm_container -v ~/.cache/huggingface:/root/.cache/huggingface --env "HUGGING_FACE_HUB_TOKEN=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" -p 8000:8000 --ipc=host vllm/vllm-openai:latest --model jCool10/jCool10-LLaMA3-VietQA-3B-merged --max-model-len 4096
