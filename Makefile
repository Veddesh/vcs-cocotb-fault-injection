# =================================================================
# Final, Explicit-Path Makefile for VCS
# =================================================================

# --- Configuration ---
SIM ?= vcs
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES  = mktest.v Counter.v SizedFIFO.v
TOPLEVEL = mktest
MODULE = test_uart
JSON_FILE = yosys.json

# --- Environment Configuration ---
# This wildcard command automatically finds the correct path to the Cocotb VPI
# library inside your virtual environment, avoiding issues with cocotb-config.
COCOTB_VPI_LIB = $(wildcard $(PWD)/cocotb_env/lib/python3.*/site-packages/cocotb/libs/libcocotbvpi_vcs.so)


# --- Main Targets ---
# The default target 'make' will clean, build, and run the simulation.
all: clean build run

# This target builds the 'simv' executable using a two-step process.
build: $(JSON_FILE)
	@echo "--- [1/2] Compiling Verilog sources with vlogan ---"
	vlogan -full64 -sverilog +define+COCOTB_SIM=1 $(VERILOG_SOURCES) -l vlogan.log

	@echo "--- [2/2] Elaborating and building 'simv' with vcs ---"
	vcs -full64 -debug_access+all +vpi -load $(COCOTB_VPI_LIB) \
		$(TOPLEVEL) -o simv -l vcs.log

# This target runs the simulation.
run:
	@echo "--- Running Simulation ---"
	./simv -l sim.log

# --- Yosys JSON Generation ---
# This rule creates the yosys.json file using the robust 'prep' command.
$(JSON_FILE): $(VERILOG_SOURCES)
	@echo "--- Generating design JSON with Yosys ---"
	@yosys -p 'read_verilog $(VERILOG_SOURCES); prep -top $(TOPLEVEL); write_json $(JSON_FILE)'

# --- Clean Rule ---
# Removes all generated files.
.PHONY: clean
clean:
	@echo "--- Cleaning generated files ---"
	@rm -rf simv simv.daidir csrc ucli.key *.log* yosys.json an.DB work *.vdb
