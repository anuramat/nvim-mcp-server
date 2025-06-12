.SILENT:
.PHONY: test

test:
	nix develop --command pytest
