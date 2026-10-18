# IndexStreamTTS Usage Guide

## Environment Preparation
### 1. Clone the Project
```bash 
git clone https://github.com/Ksuriuri/index-tts-vllm.git
```
Enter the extracted directory:
```bash
cd index-tts-vllm
```
Switch to the specified version (a historical version using VLLM 0.10.2):
```bash
git checkout 224e8d5e5c8f66801845c66b30fa765328fd0be3
```

### 2. Create and Activate a conda Environment
```bash 
conda create -n index-tts-vllm python=3.12
conda activate index-tts-vllm
```

### 3. Install PyTorch 2.8.0 (Latest Version)
#### Check the maximum CUDA version supported by the GPU and the installed version
```bash
nvidia-smi
nvcc --version
``` 
#### Maximum CUDA version supported by the driver
```bash
CUDA Version: 12.8
```
#### Actually installed CUDA compiler version
```bash
Cuda compilation tools, release 12.8, V12.8.89
```
#### The corresponding install command (PyTorch provides the CUDA 12.8 build by default)
```bash
pip install torch torchvision
```
PyTorch 2.8.0 is required (corresponding to vllm 0.10.2). For specific installation instructions, see the [PyTorch website](https://pytorch.org/get-started/locally/).

### 4. Install Dependencies
```bash 
pip install -r requirements.txt
```

### 5. Download the Model Weights
### Option 1: Download the official weight files and convert them
These are the official weight files. Download them to any local path; IndexTTS-1.5 weights are supported.
| HuggingFace                                                   | ModelScope                                                          |
|---------------------------------------------------------------|---------------------------------------------------------------------|
| [IndexTTS](https://huggingface.co/IndexTeam/Index-TTS)        | [IndexTTS](https://modelscope.cn/models/IndexTeam/Index-TTS)        |
| [IndexTTS-1.5](https://huggingface.co/IndexTeam/IndexTTS-1.5) | [IndexTTS-1.5](https://modelscope.cn/models/IndexTeam/IndexTTS-1.5) |

The ModelScope installation method is used as an example below.
#### Note: git must be installed and LFS initialized (skip if already done)
```bash
sudo apt-get install git-lfs
git lfs install
```
Create a model directory and pull the model:
```bash 
mkdir model_dir
cd model_dir
git clone https://www.modelscope.cn/IndexTeam/IndexTTS-1.5.git
```

#### Convert the model weights
```bash 
bash convert_hf_format.sh /path/to/your/model_dir
```
For example, if the downloaded IndexTTS-1.5 model is stored in the `model_dir` directory, run:
```bash
bash convert_hf_format.sh model_dir/IndexTTS-1.5
```
This converts the official model weights into a version compatible with the transformers library and saves them in the `vllm` folder under the model weights path, so the vllm library can load them later.

### 6. Adapt the API to This Project
The API response data is incompatible with the project and needs adjustment so that it returns audio data directly.
```bash
vi api_server.py
```
```bash 
@app.post("/tts", responses={
    200: {"content": {"application/octet-stream": {}}},
    500: {"content": {"application/json": {}}}
})
async def tts_api(request: Request):
    try:
        data = await request.json()
        text = data["text"]
        character = data["character"]

        global tts
        sr, wav = await tts.infer_with_ref_audio_embed(character, text)

        return Response(content=wav.tobytes(), media_type="application/octet-stream")
        
    except Exception as ex:
        tb_str = ''.join(traceback.format_exception(type(ex), ex, ex.__traceback__))
        print(tb_str)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(tb_str)
            }
        )
```

### 7. Write an sh Startup Script (run it in the appropriate conda environment)
```bash 
vi start_api.sh
```
### Paste the content below and press `:wq` to save.
#### Change `/home/system/index-tts-vllm/model_dir/IndexTTS-1.5` in the script to your actual path.
```bash
# Activate the conda environment
conda activate index-tts-vllm 
echo "Activated the project conda environment"
sleep 2
# Find the PID of the process using port 11996
PID_VLLM=$(sudo netstat -tulnp | grep 11996 | awk '{print $7}' | cut -d'/' -f1)

# Check whether a PID was found
if [ -z "$PID_VLLM" ]; then
  echo "No process using port 11996 found"
else
  echo "Found process using port 11996, PID: $PID_VLLM"
  # Try a normal kill first and wait 2 seconds
  kill $PID_VLLM
  sleep 2
  # Check whether the process is still running
  if ps -p $PID_VLLM > /dev/null; then
    echo "Process is still running; force-terminating..."
    kill -9 $PID_VLLM
  fi
  echo "Terminated process $PID_VLLM"
fi

# Find processes using VLLM::EngineCore
GPU_PIDS=$(ps aux | grep -E "VLLM|EngineCore" | grep -v grep | awk '{print $2}')

# Check whether a PID was found
if [ -z "$GPU_PIDS" ]; then
  echo "No VLLM-related process found"
else
  echo "Found VLLM-related processes, PIDs: $GPU_PIDS"
  # Try a normal kill first and wait 2 seconds
  kill $GPU_PIDS
  sleep 2
  # Check whether the process is still running
  if ps -p $GPU_PIDS > /dev/null; then
    echo "Process is still running; force-terminating..."
    kill -9 $GPU_PIDS
  fi
  echo "Terminated process $GPU_PIDS"
fi

# Create the tmp directory (if it does not exist)
mkdir -p tmp

# Run api_server.py in the background, redirecting the log to tmp/server.log
nohup python api_server.py --model_dir /home/system/index-tts-vllm/model_dir/IndexTTS-1.5 --port 11996 > tmp/server.log 2>&1 &
echo "api_server.py is running in the background; see tmp/server.log for logs"
```
Grant execute permission and run the script:
```bash 
chmod +x start_api.sh
./start_api.sh
```
Logs are written to tmp/server.log; view them with:
```bash
tail -f tmp/server.log
```
If your GPU has enough memory, you can add the `----gpu_memory_utilization` startup parameter to the script to adjust the memory usage ratio. The default is 0.25.

## Voice Configuration
index-tts-vllm supports registering custom voices through a configuration file, including single-voice and mixed-voice configurations.
Configure custom voices in the `assets/speaker.json` file in the project root.
### Configuration Format
```bash
{
    "Speaker name 1": [
        "audio_file_path_1.wav",
        "audio_file_path_2.wav"
    ],
    "Speaker name 2": [
        "audio_file_path_3.wav"
    ]
}
```
### Note (restart the service after configuring a role to register the voice)
After adding entries, add the corresponding speaker in the Control Panel (for a server-only deployment, change the corresponding voice).
