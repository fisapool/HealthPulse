#!/bin/bash

# Script to convert OSM PBF file to bzip2-compressed OSM XML format
# Note: This script was used for self-hosted Overpass API setup (now deprecated)
# The application now uses the public Overpass API

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DATA_DIR="$PROJECT_ROOT/backend/data"
PBF_FILE="$DATA_DIR/malaysia-singapore-brunei-251218.osm.pbf"
OSM_FILE="$DATA_DIR/malaysia-singapore-brunei-251218.osm"
BZ2_FILE="$DATA_DIR/malaysia-singapore-brunei-251218.osm.bz2"

echo -e "${GREEN}=== OSM PBF to OSM.BZ2 Conversion Script ===${NC}\n"

# Check if PBF file exists
if [ ! -f "$PBF_FILE" ]; then
    echo -e "${RED}Error: PBF file not found at: $PBF_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Found PBF file: $PBF_FILE${NC}"
PBF_SIZE=$(du -h "$PBF_FILE" | cut -f1)
echo -e "  File size: $PBF_SIZE\n"

# Check if output file already exists
if [ -f "$BZ2_FILE" ]; then
    echo -e "${YELLOW}Warning: Output file already exists: $BZ2_FILE${NC}"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Conversion cancelled.${NC}"
        exit 0
    fi
    echo -e "${YELLOW}Removing existing file...${NC}"
    rm -f "$BZ2_FILE" "$OSM_FILE"
fi

# Check for required tools
echo -e "\n${GREEN}Checking required tools...${NC}"

if ! command -v osmium &> /dev/null; then
    echo -e "${RED}Error: osmium-tool is not installed.${NC}"
    echo -e "Install it with: ${YELLOW}sudo apt-get install -y osmium-tool${NC}"
    exit 1
fi
echo -e "${GREEN}✓ osmium-tool is installed${NC}"

if ! command -v bzip2 &> /dev/null; then
    echo -e "${RED}Error: bzip2 is not installed.${NC}"
    echo -e "Install it with: ${YELLOW}sudo apt-get install -y bzip2${NC}"
    exit 1
fi
echo -e "${GREEN}✓ bzip2 is installed${NC}\n"

# Step 1: Convert PBF to OSM XML
echo -e "${GREEN}Step 1: Converting PBF to OSM XML...${NC}"
echo -e "This may take several minutes depending on file size...\n"

if osmium cat "$PBF_FILE" -o "$OSM_FILE"; then
    OSM_SIZE=$(du -h "$OSM_FILE" | cut -f1)
    echo -e "${GREEN}✓ Conversion complete. OSM file size: $OSM_SIZE${NC}\n"
else
    echo -e "${RED}Error: Failed to convert PBF to OSM XML${NC}"
    exit 1
fi

# Step 2: Compress OSM XML with bzip2
echo -e "${GREEN}Step 2: Compressing OSM XML with bzip2...${NC}"
echo -e "This may take several minutes...\n"

if bzip2 -v "$OSM_FILE"; then
    BZ2_SIZE=$(du -h "$BZ2_FILE" | cut -f1)
    echo -e "${GREEN}✓ Compression complete. BZ2 file size: $BZ2_SIZE${NC}\n"
else
    echo -e "${RED}Error: Failed to compress OSM file${NC}"
    exit 1
fi

# Summary
echo -e "${GREEN}=== Conversion Summary ===${NC}"
echo -e "Original PBF:  $PBF_SIZE  ($PBF_FILE)"
echo -e "Compressed:    $BZ2_SIZE  ($BZ2_FILE)"
echo -e "\n${GREEN}✓ Conversion completed successfully!${NC}"
echo -e "\nYou can now update docker-compose.yml to use:"
echo -e "  ${YELLOW}OVERPASS_PLANET_URL=file:///data/malaysia-singapore-brunei-251218.osm.bz2${NC}"


