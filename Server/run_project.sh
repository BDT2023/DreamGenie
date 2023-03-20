#!/bin/bash

start_docker ()
{
# Get the amount of free memory in kilobytes
FREE_MEM=$(free | awk '/^Mem/ {print $4}')

# Convert kilobytes to gigabytes
FREE_MEM_GB=$(echo "scale=2; $FREE_MEM/1024/1024" | bc)

# Check if free memory is less than 2 GB
if (( $(echo "$FREE_MEM_GB < 10" | bc -l) )); then
  echo "Error: Not enough free memory. Exiting script."
  exit 1
fi

echo "Free memory: $FREE_MEM_GB GB"


GPU_QUERY=$(nvidia-smi --query-gpu=index,memory.free --format=csv,noheader | sort -n -k2 | tail -n 2)

#Get the id of the gpu that has the most free memory by splitting the output using ","
GPU_ID=$(echo $GPU_QUERY | awk -F',' '{print $1}')
#Get the free memory of the gpu that has the most free memory by splitting the output using " "
GPU_MEM=$(echo $GPU_QUERY | awk -F' ' '{print $2}')
GPU_MEM_GB=$(echo "scale=2; $GPU_MEM/1024" | bc)

echo "Free GPU memory: $GPU_MEM_GB GB"

#GPU_ID=$(nvidia-smi --query-gpu=index,memory.free --format=csv,noheader | sort -n -k2 | tail -n 1 | awk -F',' '{print $1}')

if (( $(echo "$GPU_MEM_GB < 5" | bc -l) )); then
  echo "Error: Not enough GPU memory For stable diffusion. Exiting script."
  exit 1
fi


#Run docker with the aformentioned device, and with mounting the model folders from the storage
docker run -d\
 --mount type=bind,source=/home/dsi/bronfmd/sd/models/ControlNet,target=/home/foobar/stable-diffusion-webui/models/ControlNet \
 --mount type=bind,source=/home/dsi/bronfmd/sd/models/Stable-diffusion,target=/home/foobar/stable-diffusion-webui/models/Stable-diffusion \
 --mount type=bind,source=/home/dsi/bronfmd/sd/outputs,target=/home/foobar/stable-diffusion-webui/outputs,bind-propagation=shared \
 --gpus "device=$GPU_ID" --rm funkey7dan/conda-sd:no_models \
 ./webui.sh

}

start_whisper(){
# Get the two GPUs with the most free memory
GPU_QUERY=$(nvidia-smi --query-gpu=index,memory.free --format=csv,noheader | sort -n -k2 | tail -n 2)

# Get the id of the second GPU with the most free memory by splitting the output using ","
GPU_ID=$(echo $GPU_QUERY | awk -F',' '{print $1}')
# Get the free memory of the second GPU with the most free memory by splitting the output using " "
GPU_MEM=$(echo $GPU_QUERY | awk -F' ' '{print $2}')
GPU_MEM_GB=$(echo "scale=2; $GPU_MEM/1024" | bc)

if (( $(echo "$GPU_MEM_GB < 6" | bc -l) )); then
  echo "Error: Not enough GPU memory for whisper. Exiting script."
  exit 1
fi

echo "Free GPU memory: $GPU_MEM_GB GB starting whisper on $GPU_ID"

docker run -d --rm\
 --gpus="device=$GPU_ID" -p 5000:5000 whisper-api
}

start_ngrok(){
docker run --net=host -d --rm -e NGROK_AUTHTOKEN=2NFNS09sQ2z2nMSTrIkn5ZsMz80_6MsuCHbcbjzF9Abp89eGe ngrok/ngrok:latest http 5000
}

start_docker
start_whisper
start_ngrok
echo "All containers started"








