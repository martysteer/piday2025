import argparse
from nomic import atlas
from PIL import Image
from pathlib import Path
import io

def main(image_dir, map_name):
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

        # Use folder name as label
        label = path.parent.name
        data.append({
            "label": label
        })

    # Upload to Nomic Atlas
    atlas.map_data(
        blobs=blobs,
        data=data,
        identifier=map_name
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload local images to Nomic Atlas.")
    parser.add_argument('--imagedir', required=True, help="Path to the image directory")
    parser.add_argument('--mapname', required=True, help="Name of the Atlas map to create")

    args = parser.parse_args()
    main(args.imagedir, args.mapname)
