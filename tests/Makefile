TESTS = $(patsubst ./%,%,$(shell find . -maxdepth 1 -mindepth 1 -type d))
PHONY = $(TESTS)
PWD   = $(shell pwd)
PYTHON := python3

check: $(TESTS)

define test_cmd
$(1): py2-$(1) py3-$(1)

py2-$(1): FORCE
	@echo -n "Running test python2: $(1)..."
	@cd $(1); PYTHONPATH=$(PWD)/../src python2 test.py

py3-$(1):
	@echo -n "Running test python3: $(1)..."
	@cd $(1); PYTHONPATH=$(PWD)/../src python3 test.py

endef

$(foreach test,$(TESTS),$(eval $(call test_cmd,$(test))))


FORCE:

.PHONY: $(PHONY) FORCE
