#!/usr/bin/env python3
"""Module alias for 07_compare_results.py for clean Python imports."""
from importlib.machinery import SourceFileLoader
import os

target = os.path.join(os.path.dirname(__file__), "07_compare_results.py")
mod = SourceFileLoader("compare_results_mod", target).load_module()

build_blind_test_kit = mod.build_blind_test_kit
compile_comparison_report = mod.compile_comparison_report

if __name__ == "__main__":
    import runpy
    runpy.run_path(target, run_name="__main__")
