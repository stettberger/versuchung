TESTS = $(patsubst ./%,%,$(shell find . -maxdepth 1 -mindepth 1 -type d))
PHONY = $(TESTS)
PWD   = $(shell pwd)
PYTHON := python

check: $(TESTS)

define test_cmd
$(1): FORCE
	@echo -n "Running test $(1)..."
	@cd $(1); PYTHONPATH=$(PWD)/../src $(PYTHON) test.py

endef

$(foreach test,$(TESTS),$(eval $(call test_cmd,$(test))))

	
FORCE:

.PHONY: $(PHONY) FORCE
