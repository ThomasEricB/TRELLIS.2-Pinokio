#!/usr/bin/env python3
"""
Build script for TRELLIS.2 CUDA extensions.
Builds CuMesh, FlexGEMM, and o-voxel wheels with CUDA/PyTorch version in filename.
"""

import os
import sys
import subprocess
import shutil
import glob
import torch

# Get version info
TORCH_VERSION = torch.__version__.split('+')[0].replace('.', '')  # e.g., "251"
CUDA_VERSION = torch.version.cuda.replace('.', '') if torch.version.cuda else "cpu"  # e.g., "128"
PYTHON_VERSION = f"cp{sys.version_info.major}{sys.version_info.minor}"  # e.g., "cp310"

# Extensions to build
EXTENSIONS = [
    "CuMesh",
    "FlexGEMM",
    "o-voxel",
]

os.environ["DISTUTILS_USE_SDK"] = "1"

def get_script_dir():
    """Get the directory containing this script."""
    return os.path.dirname(os.path.abspath(__file__))

def clean_build_artifacts(ext_dir):
    """Remove old build artifacts."""
    for pattern in ["build", "*.egg-info", "dist"]:
        for path in glob.glob(os.path.join(ext_dir, pattern)):
            if os.path.isdir(path):
                print(f"  Removing {path}")
                shutil.rmtree(path, ignore_errors=True)

def build_extension(ext_name, extensions_dir, output_dir):
    """Build a single extension and rename the wheel."""
    ext_dir = os.path.join(extensions_dir, ext_name)
    
    if not os.path.exists(ext_dir):
        print(f"  ERROR: Extension directory not found: {ext_dir}")
        return False
    
    print(f"\n{'='*60}")
    print(f"Building {ext_name}")
    print(f"{'='*60}")
    
    # Clean old build artifacts
    print("Cleaning old build artifacts...")
    clean_build_artifacts(ext_dir)
    
    # Build the wheel
    print("Building wheel...")
    result = subprocess.run(
        ["uv", "build", "--no-build-isolation", "--wheel", 
         "--directory", "extensions", "--project", ext_name],
        cwd=os.path.dirname(extensions_dir),
        capture_output=False
    )
    
    if result.returncode != 0:
        print(f"  ERROR: Build failed for {ext_name}")
        return False
    
    # Find the built wheel
    dist_dir = os.path.join(ext_dir, "dist")
    wheels = glob.glob(os.path.join(dist_dir, "*.whl"))
    
    if not wheels:
        print(f"  ERROR: No wheel found in {dist_dir}")
        return False
    
    # Get the original wheel name and create new name with CUDA/PyTorch version
    original_wheel = wheels[0]
    wheel_name = os.path.basename(original_wheel)
    
    # Parse wheel name: name-version-python-abi-platform.whl
    parts = wheel_name.split('-')
    if len(parts) >= 5:
        pkg_name = parts[0]
        version = parts[1]
        python_tag = parts[2]
        abi_tag = parts[3]
        platform_tag = parts[4]
        
        # Create new version with CUDA/PyTorch info
        new_version = f"{version}+cu{CUDA_VERSION}.torch{TORCH_VERSION}"
        new_wheel_name = f"{pkg_name}-{new_version}-{python_tag}-{abi_tag}-{platform_tag}"
        
        # Copy to output directory with new name
        new_wheel_path = os.path.join(output_dir, new_wheel_name)
        print(f"  Copying: {wheel_name}")
        print(f"       -> {new_wheel_name}")
        shutil.copy2(original_wheel, new_wheel_path)
        
        return True
    else:
        print(f"  WARNING: Unexpected wheel name format: {wheel_name}")
        # Just copy as-is
        shutil.copy2(original_wheel, output_dir)
        return True

def main():
    script_dir = get_script_dir()
    extensions_dir = os.path.join(script_dir, "extensions")
    
    # Create output directory for wheels
    output_dir = os.path.join(script_dir, "wheels")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"TRELLIS.2 Extension Builder")
    print(f"===========================")
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA version: {torch.version.cuda}")
    print(f"Python version: {sys.version.split()[0]}")
    print(f"Output directory: {output_dir}")
    
    # Build each extension
    success_count = 0
    for ext_name in EXTENSIONS:
        if build_extension(ext_name, extensions_dir, output_dir):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"Build complete: {success_count}/{len(EXTENSIONS)} extensions built successfully")
    print(f"Wheels saved to: {output_dir}")
    print(f"{'='*60}")
    
    # List built wheels
    print("\nBuilt wheels:")
    for wheel in sorted(glob.glob(os.path.join(output_dir, "*.whl"))):
        print(f"  {os.path.basename(wheel)}")
    
    return 0 if success_count == len(EXTENSIONS) else 1

if __name__ == "__main__":
    sys.exit(main())
