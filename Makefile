# Makefile for Nomic Atlas Image Embeddings

# Configuration
API_KEY := nk-XXXX
MODEL := nomic-embed-vision-v1.5
IMAGE_DIR := images
OUTPUT_DIR := build
OUTPUT_FILE := $(OUTPUT_DIR)/embeddings.jsonl

# File extensions to process (space-separated)
EXTENSIONS := jpg jpeg png gif bmp

# Find all image files with the specified extensions
IMAGE_FILES := $(foreach ext,$(EXTENSIONS),$(wildcard $(IMAGE_DIR)/*.$(ext)))

# Generate embedding targets (one .embedding file per image)
EMBEDDING_FILES := $(patsubst $(IMAGE_DIR)/%.%,$(OUTPUT_DIR)/%.embedding,$(IMAGE_FILES))

# Generate JSON metadata targets (one .metadata.json file per image)
METADATA_FILES := $(patsubst $(IMAGE_DIR)/%.%,$(OUTPUT_DIR)/%.metadata.json,$(IMAGE_FILES))

# Generate JSONL targets (one .jsonl file per image)
JSONL_FILES := $(patsubst $(IMAGE_DIR)/%.%,$(OUTPUT_DIR)/%.jsonl,$(IMAGE_FILES))

# Default target
all: $(OUTPUT_FILE)

# Create output directory if it doesn't exist
$(OUTPUT_DIR):
	mkdir -p $(OUTPUT_DIR)

# Rule to generate embedding file from image file
$(OUTPUT_DIR)/%.embedding: $(IMAGE_DIR)/%.* | $(OUTPUT_DIR)
	@echo "Generating embedding for $<..."
	@curl -s -X POST "https://api-atlas.nomic.ai/v1/embedding/image" \
		-H "Authorization: Bearer $(API_KEY)" \
		-H "Content-Type: multipart/form-data" \
		-F "model=$(MODEL)" \
		-F "images=@$<" | \
		jq -r '.embeddings[0] | @json' > $@

# Rule to generate metadata JSON from image file
$(OUTPUT_DIR)/%.metadata.json: $(IMAGE_DIR)/%.* | $(OUTPUT_DIR)
	@echo "Extracting metadata for $<..."
	@identify -format '{\
		"filename": "%f",\
		"filepath": "$(realpath $<)",\
		"extension": "%e",\
		"size_bytes": %b,\
		"width": %w,\
		"height": %h,\
		"created": %[date:create:unix],\
		"modified": %[date:modify:unix]\
	}' $< > $@

# Rule to combine embedding and metadata into a single JSONL file
$(OUTPUT_DIR)/%.jsonl: $(OUTPUT_DIR)/%.embedding $(OUTPUT_DIR)/%.metadata.json | $(OUTPUT_DIR)
	@echo "Creating JSONL for $*..."
	@jq -n --arg id "$*" \
		--slurpfile embedding $*.embedding \
		--slurpfile metadata $*.metadata.json \
		'{"id": $$id, "embedding": $$embedding[0], "metadata": $$metadata[0]}' > $@

# Rule to combine all individual JSONL files into a single output file
$(OUTPUT_FILE): $(JSONL_FILES) | $(OUTPUT_DIR)
	@echo "Combining JSONL files into $(OUTPUT_FILE)..."
	@cat $(JSONL_FILES) > $(OUTPUT_FILE)

# Clean all generated files
clean:
	rm -rf $(OUTPUT_DIR)

# Print information about found files
info:
	@echo "Found $(words $(IMAGE_FILES)) image files:"
	@for file in $(IMAGE_FILES); do echo "  $$file"; done
	@echo "Will generate $(words $(EMBEDDING_FILES)) embedding files"
	@echo "Will generate $(words $(METADATA_FILES)) metadata files"
	@echo "Will generate $(words $(JSONL_FILES)) JSONL files"

# Display available targets
help:
	@echo "Available targets:"
	@echo "  all         - Generate embeddings for all images (default)"
	@echo "  clean       - Remove all generated files"
	@echo "  info        - Display information about found files"
	@echo "  help        - Display this help message"
	@echo ""
	@echo "Configuration variables:"
	@echo "  IMAGE_DIR   - Directory containing images (default: images)"
	@echo "  OUTPUT_DIR  - Directory for output files (default: build)"
	@echo "  OUTPUT_FILE - Final output file (default: build/embeddings.jsonl)"
	@echo "  MODEL       - Nomic embedding model (default: nomic-embed-vision-v1.5)"
	@echo "  EXTENSIONS  - Image file extensions to process (default: jpg jpeg png gif bmp)"

.PHONY: all clean info help