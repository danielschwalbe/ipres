MAINS = MajorityAssuredPR ConstitutionalStructureReform
TEX   = pdflatex
OUT   = dist

.PHONY: pdf clean

pdf:
	mkdir -p $(OUT)
	@for m in $(MAINS); do \
		$(TEX) -interaction=nonstopmode -output-directory=$(OUT) "$$m.tex"; \
		$(TEX) -interaction=nonstopmode -output-directory=$(OUT) "$$m.tex"; \
	done

clean:
	rm -rf $(OUT)
