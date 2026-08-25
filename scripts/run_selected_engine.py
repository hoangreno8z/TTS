#!/usr/bin/env python3
"""Module alias for 08_run_selected_engine.py."""
import os
import runpy

if __name__ == "__main__":
    target = os.path.join(os.path.dirname(__file__), "08_run_selected_engine.py")
    runpy.run_path(target, run_name="__main__")
