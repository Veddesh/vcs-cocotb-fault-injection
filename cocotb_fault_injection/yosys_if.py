import logging
import os
from collections import defaultdict

from cocotb.log import SimLog
from .yosys_json_parser import parse_ff_info


def setup_yosys_run_proc_mux(proc_mux):
    pass  # Deprecated

def setup_yosys_set_log_level(log_level):
    AnalyzedRTLDesign._log_level = log_level


class AnalyzedRTLDesign:
    _instance = None

    class _AnalyzedRTLDesign:
        _log_level = logging.INFO

        def __init__(self):
            self._log = SimLog(f"{self.__class__.__name__}")
            self._log.setLevel(self._log_level)

            yosys_json_path = os.getenv("YOSYS_JSON", "yosys.json")
            if not os.path.isfile(yosys_json_path):
                raise FileNotFoundError(f"Yosys JSON file not found: {yosys_json_path}")

            self._ff_info = parse_ff_info(yosys_json_path)
            self._log.info(f"Parsed flip-flop information from {yosys_json_path}")

        def get_module_ff_info(self, module_name):
            return self._ff_info[module_name]

    def __init__(self):
        if AnalyzedRTLDesign._instance is None:
            AnalyzedRTLDesign._instance = AnalyzedRTLDesign._AnalyzedRTLDesign()

    def __getattr__(self, name):
        return getattr(self._instance, name)
