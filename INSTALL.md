# Nomic Atlas Image Embedding Tool

This tool converts a directory of image files into Nomic Atlas embeddings in JSONL format.

## Installation Options

You can set up the environment using either pyenv with pipenv or a standard pip installation.

### Option 1: Using pyenv and pipenv (Recommended)

#### Step 1: Install pyenv

**On macOS:**
```bash
brew update
brew install pyenv
brew install pyenv-virtualenv
```

#### Step 2: Install Python with pyenv
```bash
# Install Python 3.10.16
pyenv install 3.10.16
pyenv virtualenv 3.10.16 piday2025
pyenv local pidate2025


```

#### Step 3: Install pipenv
Trust some certifications so package installs work.
```bash
pip config set global.trusted-host "pypi.org files.pythonhosted.org pypi.python.org"
pip install pipenv
pip install -r requirements.txt
nomic login nk-lQO-NJQXEPXmXyNc1p97qloFUhtBHSI-j9SwFOUQZC0

```

#### Step 4: Set up the project with pipenv
TODO:

```bash
# Clone or copy the project files
# Copy image_to_nomic.py and requirements.txt into this directory

# Initialize pipenv with Python version
pipenv --python $(pyenv which python)

# Install dependencies
pipenv install -r requirements.txt

# Activate the virtual environment
pipenv shell
```

#### Step 5: Run the tool

```bash
python image_to_nomic.py --input_dir /path/to/images --output_file embeddings.jsonl
```

### Option 2: Standard pip installation

If you prefer not to use pyenv and pipenv, you can use pip directly:

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python image_to_nomic.py \
  --input_dir /path/to/images \
  --output_file embeddings.jsonl \
  --extensions .jpg,.png \
  --batch_size 32 \
  --model nomic-ai/nomic-embed-vision-v1.5 \
  --device cuda \
  --metadata
```

### Command Line Arguments

- `--input_dir`, `-i`: Directory containing image files (required)
- `--output_file`, `-o`: Output JSONL file path (default: image_embeddings.jsonl)
- `--extensions`, `-e`: Comma-separated list of image extensions (default: .jpg,.jpeg,.png,.bmp,.gif)
- `--batch_size`, `-b`: Batch size for embedding generation (default: 16)
- `--max_files`, `-m`: Maximum number of files to process (optional)
- `--model`: Nomic embedding model to use (default: nomic-ai/nomic-embed-vision-v1.5)
- `--device`: Device to use (cuda/cpu, default: auto-detect)
- `--metadata`: Include file metadata in the output

## GPU Support

For faster processing, a CUDA-compatible GPU is recommended. The script will automatically use GPU acceleration if available. To use a specific GPU:

```bash
python image_to_nomic.py --input_dir /path/to/images --device cuda:0
```

## Troubleshooting

### Common Issues:

1. **CUDA Out of Memory**: Reduce batch size with `--batch_size` option
   ```bash
   python image_to_nomic.py --input_dir /path/to/images --batch_size 8
   ```

2. **Module not found errors**: Ensure all dependencies are installed
   ```bash
   pipenv install -r requirements.txt
   # or
   pip install -r requirements.txt
   ```

3. **Image loading failures**: Check that file formats are supported and not corrupted

### Checking CUDA Availability

```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA device count: {torch.cuda.device_count()}")
if torch.cuda.is_available():
    print(f"Current CUDA device: {torch.cuda.current_device()}")
    print(f"CUDA device name: {torch.cuda.get_device_name(0)}")
```