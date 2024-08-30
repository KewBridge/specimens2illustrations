# Define a list of the DOIs (resolvable article identifiers) that we want to use as input):
dois = 10.3897/phytokeys.22.4041 10.3897/phytokeys.66.8457 10.3897/phytokeys.84.12695 10.3897/phytokeys.106.21991 10.3897/phytokeys.123.31738 10.3897/phytokeys.198.79514 10.3897/phytokeys.209.87681
# Define prefixes to contruct file paths in the download and data directories
download_prefix = downloads/
data_prefix = data/
# Define a list of the files that we want to build
# xml targets will be downloaded using the DOIs defined above. Here we use functionality in make to build filenames (see https://www.gnu.org/software/make/manual/html_node/File-Name-Functions.html).
# Loop over each DOI in the list, add a prefix which is the path of the download directory, and a suffix which is the file extension ".xml"
xml_targets = $(addsuffix .xml, $(addprefix ${download_prefix}, ${dois}))
# Similar to above, loop over each DOI in the list, add a prefix which is the path of the data directory, and a suffix which is the file extension ".txt"
txt_targets = $(addsuffix /species-descriptions.txt, $(addprefix ${data_prefix}, ${dois}))
cap_targets = $(addsuffix /captions.txt, $(addprefix ${data_prefix}, ${dois}))
seg_targets = $(addsuffix /segments.txt, $(addprefix ${data_prefix}, ${dois}))

# Each .xml target depends only on the script used to download the XML data using the DOI (doi2xml.py). 
# The mkdir cmd creates the directory in which we will store output, if necessary. Here we use the dir function in make to extract the directory name from the filename of the target ($@)
# The python call accepts the dependencies of this target ($^), the "stem" - that which makes the % part of the target ie the DOI ($*) and the target itself ($@)
downloads/%.xml: doi2xml.py	
	mkdir -p $(dir $@)
	python $^ $* $@

# This is our "ultimate" target, the processed text files
all: ${cap_targets}
xml: ${xml_targets}
txt: ${txt_targets}
cap: ${cap_targets}
seg: ${seg_targets}

echo:
	echo ${xml_targets}
	echo ${txt_targets}

# Each species-descriptions.txt target depends on the script used to process the XML data (xml2illustrationdata.py) and the corresponding XML format data download
# The mkdir cmd creates the directory in which we will store output, if necessary. Here we use the dir function in make to extract the directory name from the filename of the target ($@)
# The python call accepts the dependencies of this target ($^) as the input and the target itself ($@) as the output
data/%/species-descriptions.txt: xml2illustrationdata.py downloads/%.xml
	mkdir -p $(dir $@)
	python $^ --download_images --image_dir $(dir $@) $@

# Each captions.txt target depends on the script used to extract the captions 
# (illustrations2captions.py) and the corresponding txt format 
# datafile
# The python call accepts the dependencies of this target ($^) as the input 
# and the target itself ($@) as the output
data/%/captions.txt: illustrations2captions.py data/%/species-descriptions.txt
	mkdir -p $(dir $@)
	python $^ $@

# This DOI requires special processing when working on the captions
# So this is a target which specifies the "--do_special_processing" flag 
# to the illustrations2captions.py script  
data/10.3897/phytokeys.198.79514/captions.txt: illustrations2captions.py data/10.3897/phytokeys.198.79514/species-descriptions.txt
	mkdir -p $(dir $@)
	python $^ --do_special_processing $@

# Each segments.txt target depends on the processing script (segmentimages.py)
# and its input datafiles (species-descriptions.txt and captions.txt)
# The python call accepts the dependencies of this target ($^) as the input 
# and the target itself ($@) as the output
data/%/segments.txt: segmentimages.py data/%/species-descriptions.txt data/%/captions.txt
	mkdir -p $(dir $@)
	python $^ $@

zip: build/data.zip

build/data.zip: ${txt_targets}
	mkdir -p build
	zip build/data.zip data/* -r

clean:
	rm -rf data

sterilise:
	rm -rf data downloads

# This tells make not to delete any intermediate files (see: https://www.gnu.org/software/make/manual/html_node/Special-Targets.html)
.PRECIOUS: ${xml_targets}
