ARG_PATH=~/Documents/Git/arg/src
DOC_NAME=SAND2019-CALB

DATA=\
	data/abstract.tex \
	data/introduction.tex \
	data/conclusion.tex \
	data/bibliography.tex

all: $(DOC_NAME).pdf

$(DOC_NAME).pdf: $(DOC_NAME) $(DOC_NAME).yaml data *.in
	$(ARG_PATH)/Applications/Assembler.py -s $(DOC_NAME).yaml -d data -c constants.in -o $(DOC_NAME)
	mv $(DOC_NAME)/$(DOC_NAME).pdf .

$(DOC_NAME):
	mkdir $(DOC_NAME)

clean::
	rm -fR $(DOC_NAME).pdf mutables.in $(DOC_NAME) $(ARTIFACTS) 
