from bs4 import BeautifulSoup
import argparse

def xml2illustrations(input_file, output_file):
    xml_data = None
    with open(input_file, 'r', encoding='utf8') as f_in:
        xml_data = f_in.read()
    
    # Parse the XML data using BeautifulSoup
    soup = BeautifulSoup(xml_data, 'html.parser')

    # Find all elements with tag 'tp:treatment-sec' and attribute 'sec-type="Description"'
    elements = soup.find_all('tp:treatment-sec', attrs={'sec-type': 'Description'})
    if len(elements) == 0:
        elements = soup.find_all('tp:treatment-sec', attrs={'sec-type': 'description'})

    with open(output_file, 'w', encoding='utf8') as f_out:
        for element in elements:
            output_data = [elem2TaxonName(element), elem2Description(element)] + list(elem2Figure(element))
            output_data = ['' if i is None else i for i in output_data]
            f_out.write('\t'.join(output_data) + '\n')

def elem2TaxonName(element):
    taxon_name = element.parent.find('tp:nomenclature')
    taxon_name_elements = taxon_name.find('tp:taxon-name').find_all('tp:taxon-name-part') + [element.parent.find('tp:taxon-authority')]
    taxon_name =  ' '.join([e.string for e in taxon_name_elements])
    return taxon_name

def elem2Description(element):
    description = ' '.join([e.text for e in element.find('p').contents])
    return description

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

    # Parse the command-line arguments
    args = parser.parse_args()

    # Call the main function with the provided arguments
    xml2illustrations(args.input_file, args.output_file)