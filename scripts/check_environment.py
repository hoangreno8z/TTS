#!/usr/bin/env python3
"""Hardware and Environment Audit Script for LAPQUE Personal Vietnamese TTS Studio.
Checks: OS, Python, Pip, FFmpeg, GPU, CUDA, PyTorch, VRAM, and Disk.
Does NOT install or modify drivers.
"""
import sys
import os
import platform
import shutil
import subprocess
import json

def get_os_info():
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "architecture": platform.architecture()[0]
    }

def get_python_info():
    return {
        "executable": sys.executable,
        "version": sys.version.split()[0],
        "version_full": sys.version
    }

def get_pip_info():
    try:
        res = subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True, text=True, timeout=10)
        return res.stdout.strip() if res.returncode == 0 else "Not found or error"
    except Exception as e:
        return f"Error: {e}"

def get_ffmpeg_info():
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        return {"installed": False, "path": None, "version": None}
    try:
        res = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=10)
        first_line = res.stdout.splitlines()[0] if res.stdout else "Unknown version"
        return {"installed": True, "path": ffmpeg_path, "version": first_line}
    except Exception as e:
        return {"installed": True, "path": ffmpeg_path, "version": f"Error: {e}"}

def get_disk_info(path="."):
    try:
        total, used, free = shutil.disk_usage(path)
        to_gb = 1024 ** 3
        return {
            "total_gb": round(total / to_gb, 2),
            "used_gb": round(used / to_gb, 2),
            "free_gb": round(free / to_gb, 2)
        }
    except Exception as e:
        return {"error": str(e)}

def get_nvidia_smi():
    smi_path = shutil.which("nvidia-smi")
    if not smi_path:
        return {"available": False, "details": "nvidia-smi not found in PATH"}
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free,driver_version", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10
        )
        if res.returncode == 0:
            gpus = []
            for line in res.stdout.strip().splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 4:
                    gpus.append({
                        "name": parts[0],
                        "total_memory_mb": parts[1],
                        "free_memory_mb": parts[2],
                        "driver_version": parts[3]
                    })
            return {"available": True, "gpus": gpus}
        else:
            return {"available": False, "details": res.stderr.strip()}
    except Exception as e:
        return {"available": False, "details": f"Error: {e}"}

def get_pytorch_info():
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        gpu_count = torch.cuda.device_count() if cuda_available else 0
        devices = []
        if cuda_available:
            for i in range(gpu_count):
                devices.append({
                    "index": i,
                    "name": torch.cuda.get_device_name(i),
                    "capability": torch.cuda.get_device_capability(i),
                    "total_memory_gb": round(torch.cuda.get_device_properties(i).total_memory / (1024**3), 2)
                })
        return {
            "installed": True,
            "version": torch.__version__,
            "cuda_available": cuda_available,
            "cuda_version": torch.version.cuda if hasattr(torch.version, 'cuda') else None,
            "cudnn_version": torch.backends.cudnn.version() if hasattr(torch.backends, 'cudnn') and torch.backends.cudnn.is_available() else None,
            "device_count": gpu_count,
            "devices": devices
        }
    except ImportError:
        return {"installed": False, "error": "PyTorch is not installed in the current Python environment"}
    except Exception as e:
        return {"installed": False, "error": str(e)}

def audit_environment():
    report = {
        "os": get_os_info(),
        "python": get_python_info(),
        "pip": get_pip_info(),
        "ffmpeg": get_ffmpeg_info(),
        "disk": get_disk_info("."),
        "nvidia_smi": get_nvidia_smi(),
        "pytorch": get_pytorch_info()
    }
    return report

def format_human_report(rep):
    lines = []
    lines.append("=" * 60)
    lines.append("LAPQUE PERSONAL TTS — HARDWARE & ENVIRONMENT AUDIT REPORT")
    lines.append("=" * 60)
    lines.append(f"Operating System : {rep['os']['system']} {rep['os']['release']} ({rep['os']['machine']})")
    lines.append(f"Python           : {rep['python']['version']} ({rep['python']['executable']})")
    lines.append(f"Pip              : {rep['pip']}")
    lines.append(f"FFmpeg           : {'Installed (' + rep['ffmpeg']['version'] + ')' if rep['ffmpeg']['installed'] else 'NOT FOUND'}")
    lines.append(f"Disk Space       : Total: {rep['disk']['total_gb']} GB | Free: {rep['disk']['free_gb']} GB")
    
    lines.append("\n--- GPU & CUDA (via nvidia-smi) ---")
    if rep['nvidia_smi']['available'] and rep['nvidia_smi']['gpus']:
        for i, g in enumerate(rep['nvidia_smi']['gpus']):
            lines.append(f"GPU [{i}]          : {g['name']}")
            lines.append(f"VRAM             : Total {g['total_memory_mb']} MB | Free {g['free_memory_mb']} MB")
            lines.append(f"Driver Version   : {g['driver_version']}")
    else:
        lines.append(f"Status           : {rep['nvidia_smi'].get('details', 'No NVIDIA GPU detected via nvidia-smi')}")

    lines.append("\n--- PyTorch & CUDA ---")
    if rep['pytorch']['installed']:
        lines.append(f"PyTorch Version  : {rep['pytorch']['version']}")
        lines.append(f"CUDA Available   : {rep['pytorch']['cuda_available']}")
        lines.append(f"PyTorch CUDA Ver : {rep['pytorch']['cuda_version']}")
        if rep['pytorch']['cuda_available']:
            for d in rep['pytorch']['devices']:
                lines.append(f"Device [{d['index']}]       : {d['name']} ({d['total_memory_gb']} GB VRAM)")
    else:
        lines.append(f"Status           : {rep['pytorch']['error']}")

    lines.append("=" * 60)
    
    # Strategy recommendation
    lines.append("\nSTRATEGY RECOMMENDATION:")
    cuda_ok = rep['pytorch'].get('cuda_available', False) or (rep['nvidia_smi']['available'] and len(rep['nvidia_smi']['gpus']) > 0)
    if cuda_ok:
        lines.append("-> Local GPU is available. Local development & inference recommended.")
    else:
        lines.append("-> No local CUDA GPU detected. Google Colab Free Tier (T4 GPU) recommended for model benchmark/inference, while Text Normalizer & API development run locally.")
    lines.append("=" * 60)
    return "\n".join(lines)

if __name__ == "__main__":
    rep = audit_environment()
    print(format_human_report(rep))
    # Save json result
    out_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(out_dir)
    json_path = os.path.join(project_root, "docs", "environment_audit.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2, ensure_ascii=False)
    print(f"\nSaved raw audit JSON to: {json_path}")
