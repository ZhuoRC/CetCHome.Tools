#!/usr/bin/env python3

import os
import sys
from PIL import Image
from datetime import datetime
import argparse

def merge_images_to_pdf(input_folder, output_folder):
    """
    Merge all images from input folder into a single PDF file.
    
    Args:
        input_folder (str): Path to folder containing images
        output_folder (str): Path to folder where PDF will be saved
    """
    
    # Supported image formats
    supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif')
    
    # Get all image files from input folder
    image_files = []
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(supported_formats):
            image_files.append(os.path.join(input_folder, filename))
    
    if not image_files:
        print(f"No supported image files found in {input_folder}")
        print(f"Supported formats: {', '.join(supported_formats)}")
        return False
    
    # Sort files to ensure consistent order
    image_files.sort()
    
    print(f"Found {len(image_files)} image(s) to merge:")
    for img_file in image_files:
        print(f"  - {os.path.basename(img_file)}")
    
    try:
        # Open and convert images
        images = []
        for img_path in image_files:
            img = Image.open(img_path)
            # Convert to RGB if necessary (for PDF compatibility)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            images.append(img)
        
        # Create output filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"merged_images_{timestamp}.pdf"
        output_path = os.path.join(output_folder, output_filename)
        
        # Save as PDF
        if images:
            images[0].save(output_path, save_all=True, append_images=images[1:])
            print(f"\nSuccess! PDF created: {output_path}")
            return True
        
    except Exception as e:
        print(f"Error creating PDF: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Merge multiple images into a single PDF')
    parser.add_argument('--input', '-i', default='input', 
                       help='Input folder containing images (default: input)')
    parser.add_argument('--output', '-o', default='output', 
                       help='Output folder for PDF file (default: output)')
    
    args = parser.parse_args()
    
    input_folder = args.input
    output_folder = args.output
    
    # Check if input folder exists
    if not os.path.exists(input_folder):
        print(f"Error: Input folder '{input_folder}' does not exist")
        sys.exit(1)
    
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    print(f"Input folder: {input_folder}")
    print(f"Output folder: {output_folder}")
    print("-" * 50)
    
    # Merge images to PDF
    success = merge_images_to_pdf(input_folder, output_folder)
    
    if success:
        print("\nOperation completed successfully!")
    else:
        print("\nOperation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()