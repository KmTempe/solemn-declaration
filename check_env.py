#!/usr/bin/env python3
"""
Virtual Environment and Python Update Checker
"""
import sys
import pkg_resources
import subprocess
import json
from pathlib import Path

def check_python_version():
    """Check current Python version"""
    print(f"🐍 Current Python: {sys.version}")
    print(f"📍 Python Location: {sys.executable}")
    print(f"🎯 Python Version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

def check_virtual_environment():
    """Check if we're in a virtual environment"""
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if in_venv:
        print("✅ Running in virtual environment")
        print(f"📂 Virtual Environment: {sys.prefix}")
    else:
        print("❌ NOT running in virtual environment")
        print("⚠️  This could affect global Python packages")
    
    return in_venv

def check_dependencies():
    """Check installed dependencies"""
    try:
        # Read requirements.txt
        requirements_file = Path("requirements.txt")
        if not requirements_file.exists():
            print("❌ requirements.txt not found")
            return False
        
        print("\n📦 Checking dependencies from requirements.txt:")
        
        with open(requirements_file, 'r') as f:
            requirements = [line.strip() for line in f.readlines() 
                          if line.strip() and not line.startswith('#')]
        
        installed_packages = {pkg.project_name.lower(): pkg.version 
                            for pkg in pkg_resources.working_set}
        
        missing = []
        outdated = []
        
        for req in requirements:
            if '==' in req:
                package_name, required_version = req.split('==')
                package_name = package_name.lower()
                
                if package_name in installed_packages:
                    installed_version = installed_packages[package_name]
                    if installed_version == required_version:
                        print(f"  ✅ {package_name}: {installed_version}")
                    else:
                        print(f"  ⚠️  {package_name}: {installed_version} (required: {required_version})")
                        outdated.append(f"{package_name}=={required_version}")
                else:
                    print(f"  ❌ {package_name}: NOT INSTALLED")
                    missing.append(req)
        
        if missing:
            print(f"\n❌ Missing packages: {len(missing)}")
            for pkg in missing:
                print(f"  - {pkg}")
        
        if outdated:
            print(f"\n⚠️  Version mismatches: {len(outdated)}")
            for pkg in outdated:
                print(f"  - {pkg}")
        
        if not missing and not outdated:
            print("\n✅ All dependencies are correctly installed!")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Error checking dependencies: {e}")
        return False

def main():
    print("🔍 Virtual Environment & Python Update Checker")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    print()
    
    # Check virtual environment
    in_venv = check_virtual_environment()
    print()
    
    # Check dependencies
    deps_ok = check_dependencies()
    print()
    
    # Summary
    print("📋 Summary:")
    print(f"  • Virtual Environment: {'✅' if in_venv else '❌'}")
    print(f"  • Dependencies: {'✅' if deps_ok else '⚠️'}")
    
    if not in_venv:
        print("\n🚀 To create and use virtual environment:")
        print("  1. python -m venv venv")
        print("  2. .\\venv\\Scripts\\Activate.ps1  (Windows)")
        print("  3. pip install -r requirements.txt")
    
    if not deps_ok:
        print("\n🔧 To fix dependencies:")
        print("  pip install -r requirements.txt --upgrade")

if __name__ == "__main__":
    main()
