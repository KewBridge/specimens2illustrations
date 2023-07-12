dois = 10.3897/phytokeys.22.4041 10.3897/phytokeys.66.8457 10.3897/phytokeys.84.12695 10.3897/phytokeys.106.21991 10.3897/phytokeys.123.31738 10.3897/phytokeys.198.79514 10.3897/phytokeys.209.87681
data_prefix = data/
download_prefix = downloads/
xml_targets = $(addsuffix .xml, $(addprefix ${download_prefix}, ${dois}))
txt_targets = $(addsuffix .txt, $(addprefix ${data_prefix}, ${dois}))

.PRECIOUS: ${xml_targets}

downloads/%.xml:
	mkdir -p $(dir $@)
	python doi2xml.py $* $@

all: ${txt_targets}

data/%.txt: xml2illustrationdata.py downloads/%.xml
	mkdir -p $(dir $@)
	python $^ $@

clean:
	rm -rf data

sterilise:
	rm -rf data downloads