import argparse
import keras_ocr
import pandas as pd
import os
import cv2

from functions.imageFunctions import extractAllImages, isGrayImage
from functions.segmentationFunctions import segmentColorImage, segmentGrayImage

def main(inputfile_species, inputfile_captions, outputfile):
    
    df = pd.read_csv(inputfile_captions, header=0, index_col=[0,1], encoding='utf-8')
    
    count_per_row = df.groupby(level = 0, axis = 0).size().values
    
    pipeline = keras_ocr.pipeline.Pipeline()
    
    for correct_count, (image, image_name) in zip(count_per_row, extractAllImages(inputfile_species)):
        
        # If correct_count is 1, then no segmentation is needed
        if correct_count == 1:
            continue
                    
        labels = [chr(97 + i ) for i in range(correct_count)]
        
        if isGrayImage(image):
            
            prediction = pipeline.recognize([image])
            
            segments = segmentGrayImage(image, prediction, labels)
            
        else:
            
            segments = segmentColorImage(image)
            
            
        for label in segments:
            
            segment = segments[label]
            
            segment_name = image_name.split('.')[0] + f'-{label.upper()}.jpg'
            save_path = os.path.join(outputfile, segment_name)
            
            cv2.imwrite(save_path, segment)
            
    print('''Segmenting images specified in {}, using caption 
          data from {} writing segment metadata to {}'''
          .format(inputfile_species, inputfile_captions, outputfile))


if __name__ == "__main__":
    
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description="Process captions.")

    # Add the command-line arguments
    parser.add_argument("input_file_species", help="Path to the input species datafile")
    parser.add_argument("input_file_captions", help="Path to the input caption datafile")
    parser.add_argument("output_file", help="Path to the output segment metadata file")

    # Parse the command-line arguments
    args = parser.parse_args()

    # Call the main function with the provided arguments
    main(args.input_file_species, args.input_file_captions, args.output_file)
