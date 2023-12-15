import argparse

def main(inputfile, outputfile, segment_images=False):
    print('Parsing captions in {} saving parsed caption data to {}'.format(inputfile, outputfile))

if __name__ == "__main__":
    
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description="Process captions.")

    # Add the command-line arguments
    parser.add_argument("input_file", help="Path to the input txt file")
    parser.add_argument("output_file", help="Path to the output captions file")

    # Parse the command-line arguments
    args = parser.parse_args()

    # Call the main function with the provided arguments
    main(args.input_file, args.output_file)
