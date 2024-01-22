from bs4 import BeautifulSoup
import requests
import os
import argparse
import datetime
import random

import sys
sys.path.append('sepcimens2illustrations/functions')
from figureFunctions import getLabel, getUrl, figureSegmentation, standartizeFigureLabel
from pandasFunctions import df2Excel

def xml2illustrations(input_file, output_file, image_dir, download_images = True):
    xml_data = None
    with open(input_file, 'r', encoding = 'utf-8') as f_in:
        
            xml_data = f_in.read()
            
            soup = BeautifulSoup(xml_data, 'xml')
            
            all_figures = soup.find_all('fig')
            
            # Distribution Figures are always maps that 
            # are ALWAYS unwanted in our algorithms
            distribution_figures = [figure for figure in all_figures \
                                    if figure.find_all(string=re.compile('distribution', re.IGNORECASE))]
            
            wanted_figures = [figure for figure in all_figures \
                              if figure not in distribution_figures]
            
            search_table = figureSegmentation(wanted_figures)
            
            #Temporary as we are only working on 'Description' tagged figures for now
            key = 'Description'
            description_figures = search_table.get(key, [])
                        
            with open(output_file, 'w', encoding='utf8') as f_out:
                for i, figure in enumerate(description_figures):
                    
                    if download_images:
                        
                        os.makedirs(image_dir, exist_ok = True)
                        fig_url = getUrl(figure)
                        
                        if fig_url is not None:
                            
                            figure_label = ''.join(filter(str.isdigit(getLabel(figure))))
                            figure_label = standartizeFigureLabel(figure_label)
                            
                            image_file = f'{key}{i}_{figure_label}.jpg'
                            save_path = os.path.join(image_dir, image_file)
                            
                            downloadImage(fig_url, save_path)
            f_out.close()
            
            excel_name = 'plant-data.xlsx'
            # Write plant data into output_file
            df2Excel(search_table.get('Descripiton', []), output_file, excel_name)
            
# TODO: Use the requests library to download the image specified in fig_url and store the downloaded file in image_dir

def downloadImage(url, destinationDir):  
    r = requests.get(url)
    #print("Url:",url)
    with open(destinationDir, 'wb') as img_f:
        img_f.write(r.content)
        #print(img_f)
        
if __name__ == "__main__":
    
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description="Process input and output files.")

    # Add the command-line arguments
    parser.add_argument("input_file", help="Path to the input XML format article file")
    parser.add_argument("output_file", help="Path to the output file")
    parser.add_argument("--image_dir", help="Path to the directory used to store downloaded images")
    parser.add_argument("--download_images", dest='download_images', default=False, action='store_true')
    
    # Parse the command-line arguments
    args = parser.parse_args()

    # Call the main function with the provided arguments
    xml2illustrations(args.input_file, args.output_file, args.image_dir,  args.download_images)
