from nomic import atlas
from PIL import Image
from pathlib import Path
import io

# Path to image directory
image_dir = 'data/test'  # Update to your actual path

# Get image paths
image_paths = list(Path(image_dir).rglob("*.[jp][pn]g"))  # jpg, jpeg, png

blobs = []
data = []

for path in image_paths:
    # Load image and convert to byte array
    with Image.open(path) as img:
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        blobs.append(img_byte_arr.getvalue())

    # Use folder name as label (assumes structure like data/images/cat/image1.jpg)
    label = path.parent.name
    data.append({
        "filename": path.name,
        "label": label
    })

# Upload to Nomic Atlas
atlas.map_data(
    blobs=blobs,
    data=data,
    identifier="Local-Image-Upload-With-Labels"
)

# print(data)