from bs4 import BeautifulSoup
import requests
import os
import argparse
import datetime
import random

def xml2illustrations(input_file, output_file, image_dir, download_images = True):
    xml_data = None
    with open(input_file, 'r', encoding = 'utf-8') as f_in:
            xml_data = f_in.read()
            
            soup = BeautifulSoup(xml_data, 'xml')
            
            elements = soup.find_all('tp:treatment-sec', attrs={'sec-type': 'Description'})
            if len(elements) == 0:
                elements = soup.find_all('tp:treatment-sec', attrs={'sec-type': 'description'})
            #print(len(elements))
            
            with open(output_file, 'w', encoding='utf8') as f_out:
                for element in elements:
                    (fig_label, caption, fig_url) = elem2Figure(element)
                    output_data = [elem2TaxonName(element), elem2Description(element), fig_label, caption, fig_url]
                    output_data = ['' if i is None else i for i in output_data]
                    f_out.write('\t'.join(output_data) + '\n')
                    if download_images:
                        os.makedirs(image_dir, exist_ok = True)
                        random_component = "{:04x}".format(random.randint(0, 900000))
                        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                        image_file = f"image_{timestamp}_{random_component}.jpg"
                        save_path = os.path.join(image_dir, image_file)
                        if fig_url is not None:
                            downloadImage(fig_url, save_path)
            
# TODO: Use the requests library to download the image specified in fig_url and store the downloaded file in image_dir

def downloadImage(url, destinationDir):  
    r = requests.get(url)
    #print("Url:",url)
    with open(destinationDir, 'wb') as img_f:
        img_f.write(r.content)
        #print(img_f)
        
def elem2Description(element):
    description = ' '.join([e.text for e in element.find('p').contents])
    return description                
                
def elem2TaxonName(element):
    taxon_name = element.parent.find('tp:nomenclature')
    taxon_name_elements = taxon_name.find('tp:taxon-name').find_all('tp:taxon-name-part') + [element.parent.find('tp:taxon-authority')]
    taxon_name =  ' '.join([e.string for e in taxon_name_elements])
    return taxon_name

def elem2Figure(element):
    fig_label = None
    caption = None
    fig_url = None
    if element.find('fig') is not None:
        fig_label = element.find('fig').find('label').string
        caption =  ' '.join([e.text for e in element.find('fig').find('caption').find('p').contents])
        fig_url = element.find('fig').find('uri', attrs={'content-type':'original_file'}).string
    return (fig_label, caption, fig_url)


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
