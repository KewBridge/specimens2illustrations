import argparse

def main(inputfile_species, inputfile_captions, outputfile):
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
