ARG_PATH=/Users/pppebay/Documents/Git/arg/src
DOC_NAME=SAND2019-LBS

DATA=\
	data/NodeGossiper-n4096-p16-o10000-uniform-f6-t1_0--0s-52s.png \
	data/NodeGossiper-n4096-p16-o10000-uniform-f6-t1_0--25s-52s.png \
	data/abstract.tex \
	data/introduction.tex \
	data/informed_transfer.tex \
	data/theory_modified_criterion.tex \
	data/results_modified_criterion.tex

all: $(DOC_NAME).pdf

$(DOC_NAME).pdf: $(DOC_NAME) $(DOC_NAME).yaml data *.in
	$(ARG_PATH)/Applications/Assembler.py -s $(DOC_NAME).yaml -d data -r SAND -c constants.in -a abstract.tex -o $(DOC_NAME)
	mv $(DOC_NAME)/$(DOC_NAME).pdf .

$(DOC_NAME):
	mkdir $(DOC_NAME)

clean::
	rm -fR $(DOC_NAME).pdf mutables.in $(DOC_NAME) $(ARTIFACTS) 
