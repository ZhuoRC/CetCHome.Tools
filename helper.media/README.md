# Image to PDF Merger

A Python application that merges multiple pictures from an input folder into a single PDF file and saves it to an output folder.

## Features

- Supports common image formats: PNG, JPG, JPEG, BMP, TIFF, GIF
- Automatically creates output folder if it doesn't exist
- Sorts images alphabetically for consistent ordering
- Adds timestamp to output PDF filename
- Command-line interface with customizable input/output folders

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage
Place your images in the `input` folder and run:
```bash
python merge_images_to_pdf.py
```

The merged PDF will be saved in the `output` folder.

### Custom Folders
```bash
python merge_images_to_pdf.py --input /path/to/images --output /path/to/output
```

### Command Line Options
- `--input` or `-i`: Specify input folder (default: `input`)
- `--output` or `-o`: Specify output folder (default: `output`)

## Example
```bash
# Using default folders
python merge_images_to_pdf.py

# Using custom folders
python merge_images_to_pdf.py -i "C:\My Images" -o "C:\My PDFs"
```

## Output
The application creates a PDF file with a timestamp in the filename:
- Format: `merged_images_YYYYMMDD_HHMMSS.pdf`
- Example: `merged_images_20241214_143022.pdf`