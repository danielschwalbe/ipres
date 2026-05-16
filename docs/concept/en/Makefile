MAIN = MajorityAssuredPR
TEX  = pdflatex
OUT  = dist

.PHONY: pdf clean

pdf:
	mkdir -p $(OUT)
	$(TEX) -interaction=nonstopmode -output-directory=$(OUT) $(MAIN).tex
	$(TEX) -interaction=nonstopmode -output-directory=$(OUT) $(MAIN).tex

clean:
	rm -rf $(OUT)
