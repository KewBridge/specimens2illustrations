import argparse
import os.path
import requests


def doi2xml(doi, output_file):
    # Get actual url 
    r = requests.get('https://doi.org/' + doi)
    url = r.url
    # Get article ID:
    article_id = phytokeysurl2articleid(url)
    # Get XML
    url = 'https://phytokeys.pensoft.net/article/{article_id}/download/xml/'.format(article_id=article_id)
    r = requests.get(url)
    # Save to file
    with open(output_file, 'w', encoding='utf8') as f_out:
        f_out.write(r.text)
    
def phytokeysurl2articleid(url):
    articleid = None
    if url is not None:
        if '?id=' in url:
            article_id = url.split('?id=',1)[-1]
        elif '/article/' in url:
            article_id = url.split('article/',1)[-1]
            if article_id.endswith('/'):
                article_id = article_id[:-1]
    return article_id


if __name__ == "__main__":
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description="Process DOI and save XML format article in output file.")

    # Add the command-line arguments
    parser.add_argument("doi", help="Phytokeys DOI to be downloaded")
    parser.add_argument("output_file", help="Path to the output file")

    # Parse the command-line arguments
    args = parser.parse_args()

    # Call the main function with the provided arguments
    doi2xml(args.doi, args.output_file)
