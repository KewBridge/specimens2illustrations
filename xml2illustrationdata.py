from bs4 import BeautifulSoup
import requests
import os
import argparse

import sys
sys.path.append('./functions/figureFunctions')
from functions.figureFunctions import getLabel, getUrl, getTaxonName, getDescription, figureSegmentation
    
def xml2illustrations(input_file, output_file, image_dir, download_images = True):
    xml_data = None
    with open(input_file, 'r', encoding = 'utf-8') as f_in:
        
            xml_data = f_in.read()
            
            soup = BeautifulSoup(xml_data, 'xml')
            
            all_figures = soup.find_all('fig')
            
            search_table = figureSegmentation(all_figures)
            
            #Temporary as we are only working on 'Description' tagged figures for now
            key = 'Description'
            description_figures = search_table.get(key, [])
                        
            with open(output_file, 'w', encoding='utf-8') as f_out:
                
                headers = ['Label', 'Taxon Name', 'Description', 'Url', 'Figure Object']
                f_out.write('\t'.join(headers) + '\n')
                
                for i, figure in enumerate(description_figures):

                    # Eliminate incorrect tagging in articles
                    if 'Distribution of' in figure.text:
                        continue
                        
                    output_data = [getLabel(figure), getTaxonName(figure), getDescription(figure), getUrl(figure), str(figure).replace('\n', '')]
                    
                    output_data = ['' if i is None else i for i in output_data]
                    f_out.write('\t'.join(output_data) + '\n')
                    
                    if download_images:
                        
                        os.makedirs(image_dir, exist_ok = True)
                        fig_url = getUrl(figure)
                        
                        if fig_url is not None:
                            
                            figure_label = ''.join(filter(str.isdigit, getLabel(figure)))
                            figure_label = '0' * (3 - len(figure_label)) + figure_label  
                            
                            image_file = f'{key}_{figure_label}.jpg'
                            save_path = os.path.join(image_dir, image_file)
                            
                            downloadImage(fig_url, save_path)
            f_out.close()

        
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
