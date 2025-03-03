#!/bin/bash
# embed-images.sh - Convert image files to Nomic Atlas embeddings in JSONL format
# Usage: ./embed-images.sh [-h] [-o OUTPUT_FILE] [-e EXTENSIONS] [-m MODEL] INPUT_DIR

set -e

# Default values
OUTPUT_FILE="image_embeddings.jsonl"
EXTENSIONS=".jpg,.jpeg,.png,.bmp,.gif"
MODEL="nomic-embed-vision-v1.5"
API_KEY="nk-XXXXX"
INCLUDE_METADATA=true

# Function to display usage
show_help() {
    echo "Usage: $0 [-h] [-o OUTPUT_FILE] [-e EXTENSIONS] [-m MODEL] INPUT_DIR"
    echo ""
    echo "Convert image files to Nomic Atlas embeddings in JSONL format."
    echo ""
    echo "Positional arguments:"
    echo "  INPUT_DIR             Directory containing image files"
    echo ""
    echo "Optional arguments:"
    echo "  -h, --help            Show this help message and exit"
    echo "  -o, --output-file     Output JSONL file path (default: image_embeddings.jsonl)"
    echo "  -e, --extensions      Comma-separated list of image file extensions (default: .jpg,.jpeg,.png,.bmp,.gif)"
    echo "  -m, --model           Nomic embedding model to use (default: nomic-embed-vision-v1.5)"
    echo "  -n, --no-metadata     Don't include file metadata in the output"
    echo ""
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            ;;
        -o|--output-file)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -e|--extensions)
            EXTENSIONS="$2"
            shift 2
            ;;
        -m|--model)
            MODEL="$2"
            shift 2
            ;;
        -n|--no-metadata)
            INCLUDE_METADATA=false
            shift
            ;;
        *)
            INPUT_DIR="$1"
            shift
            ;;
    esac
done

# Check if input directory is provided
if [ -z "$INPUT_DIR" ]; then
    echo "Error: Input directory is required."
    show_help
fi

# Check if input directory exists
if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory $INPUT_DIR does not exist."
    exit 1
fi

# Convert comma-separated extensions to find pattern
FIND_PATTERN=""
IFS=',' read -ra EXT_ARRAY <<< "$EXTENSIONS"
for ext in "${EXT_ARRAY[@]}"; do
    FIND_PATTERN+=" -o -name \"*$ext\""
done
FIND_PATTERN=${FIND_PATTERN:3}  # Remove the leading " -o"

# Create or truncate output file
> "$OUTPUT_FILE"

# Find all image files
echo "Finding image files in $INPUT_DIR with extensions: $EXTENSIONS"
IMAGE_FILES=$(eval "find \"$INPUT_DIR\" -type f \( $FIND_PATTERN \)")

# Count total files
TOTAL_FILES=$(echo "$IMAGE_FILES" | wc -l)
echo "Found $TOTAL_FILES image files to process"

# Process each file
COUNT=0
echo "$IMAGE_FILES" | while IFS= read -r file; do
    if [ -z "$file" ]; then
        continue
    fi
    
    COUNT=$((COUNT + 1))
    echo "[$COUNT/$TOTAL_FILES] Processing: $file"
    
    # Get file metadata
    FILENAME=$(basename "$file")
    FILEPATH=$(realpath "$file")
    EXTENSION="${FILENAME##*.}"
    SIZE_BYTES=$(stat -f "%z" "$file" 2>/dev/null || stat -c "%s" "$file" 2>/dev/null)
    CREATED=$(stat -f "%B" "$file" 2>/dev/null || stat -c "%W" "$file" 2>/dev/null)
    MODIFIED=$(stat -f "%m" "$file" 2>/dev/null || stat -c "%Y" "$file" 2>/dev/null)
    
    # Generate embedding via Nomic API
    RESPONSE=$(curl -s -X POST "https://api-atlas.nomic.ai/v1/embedding/image" \
        -H "Authorization: Bearer $API_KEY" \
        -H "Content-Type: multipart/form-data" \
        -F "model=$MODEL" \
        -F "images=@$file")
    
    # Check if the API call was successful
    if echo "$RESPONSE" | jq -e '.embeddings' > /dev/null; then
        # Extract embedding
        EMBEDDING=$(echo "$RESPONSE" | jq -c '.embeddings[0]')
        
        # Create JSON object for this image
        if [ "$INCLUDE_METADATA" = true ]; then
            # With metadata
            JSON_OBJECT=$(jq -n \
                --arg id "${FILENAME%.*}" \
                --argjson embedding "$EMBEDDING" \
                --arg filename "$FILENAME" \
                --arg filepath "$FILEPATH" \
                --arg extension ".$EXTENSION" \
                --arg size_bytes "$SIZE_BYTES" \
                --arg created "$CREATED" \
                --arg modified "$MODIFIED" \
                '{
                    id: $id,
                    embedding: $embedding,
                    metadata: {
                        filename: $filename,
                        filepath: $filepath,
                        extension: $extension,
                        size_bytes: ($size_bytes | tonumber),
                        created: ($created | tonumber),
                        modified: ($modified | tonumber)
                    }
                }')
        else
            # Without metadata
            JSON_OBJECT=$(jq -n \
                --arg id "${FILENAME%.*}" \
                --argjson embedding "$EMBEDDING" \
                '{
                    id: $id,
                    embedding: $embedding
                }')
        fi
        
        # Append to output file
        echo "$JSON_OBJECT" >> "$OUTPUT_FILE"
    else
        echo "Error processing $file: $(echo "$RESPONSE" | jq -r '.detail // "Unknown error"')"
    fi
done

echo "Successfully processed images and saved embeddings to $OUTPUT_FILE"