TESTS = $(patsubst ./%,%,$(shell find . -maxdepth 1 -mindepth 1 -type d))
PHONY = $(TESTS)
PWD   = $(shell pwd)
PYTHON ?= python3

check: $(TESTS)

define test_cmd
$(1): py-$(1)

py-$(1):
	@echo -n "Running test: $(1)..."
	@cd $(1); PYTHONPATH=$(PWD)/.. ${PYTHON} test.py

endef

$(foreach test,$(TESTS),$(eval $(call test_cmd,$(test))))


FORCE:

.PHONY: $(PHONY) FORCE
