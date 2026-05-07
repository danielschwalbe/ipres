MAIN = MehrheitsVerhältniswahl
TEX  = pdflatex

.PHONY: pdf clean

pdf:
	$(TEX) -interaction=nonstopmode $(MAIN).tex
	$(TEX) -interaction=nonstopmode $(MAIN).tex

clean:
	rm -f *.aux *.log *.toc *.out *.pdf
