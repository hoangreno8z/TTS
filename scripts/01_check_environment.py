#!/usr/bin/env python3
"""Wrapper calling check_environment.py."""
import runpy
import os

if __name__ == "__main__":
    target = os.path.join(os.path.dirname(__file__), "check_environment.py")
    runpy.run_path(target, run_name="__main__")
