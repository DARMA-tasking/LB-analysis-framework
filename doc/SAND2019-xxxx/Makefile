ARG_PATH=/Users/pppebay/Documents/Git/arg/src
DOC_NAME=SAND2019-LBS

DATA=\
	data/Grapevine-n4096-p16-o10000-uniform-i10-k10-f6-t1_0.png \
	data/Grapevine-n4096-p16-o10000-uniform-i10-k10-f6-t1_0.tex \
	data/NodeGossiper-n4096-p16-o10000-uniform-i10-k10-f6-t1_0.png \
	data/NodeGossiper-n4096-p16-o10000-uniform-i10-k10-f6-t1_0.tex \
	data/NodeGossiper-n4096-p16-o10000-uniform-f6-t1_0--0s-52s.png \
	data/NodeGossiper-n4096-p16-o10000-uniform-f6-t1_0--0s-52s.tex \
	data/NodeGossiper-n8-lstats-i5-k4-f4-t1_0.0-vom.png \
	data/NodeGossiper-n8-lstats-i5-k4-f4-t1_0.0-vom.tex \
	data/Grapevine-n8-lstats-i5-k4-f4-t1_0.0-vom.png \
	data/Grapevine-n8-lstats-i5-k4-f4-t1_0.0-vom.tex \
	data/NodeGossiper_moves.tex \
	data/Grapevine_moves.tex \
	data/abstract.tex \
	data/introduction.tex \
	data/informed_transfer.tex \
	data/problem_modified_criterion.tex \
	data/theory_modified_criterion.tex \
	data/results_modified_criterion.tex \
	data/comparison-i-k.tex \
	data/equi_distribution.tex \
	data/dirac_distribution.tex \
	data/optimal_distribution.tex \
	data/object_iso_load.tex \
	data/approximate_iso_load.tex \
	data/application.tex \
	data/experimental_setting.tex \
	data/experimental_statistics.tex \
	data/comparative_results.tex \
	data/prescribed_object_moves.tex \
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
