#!/usr/bin/env python3
"""
Python script to install dependencies for Odoo Instance Provisioning Module
Usage: python3 install_dependencies.py
"""

import subprocess
import sys
import importlib.util
import os

def check_package(package_name):
    """Check if a Python package is installed"""
    spec = importlib.util.find_spec(package_name)
    return spec is not None

def install_package(package_name):
    """Install a Python package using pip"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_name, '--user'])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    print("🚀 Installing Python dependencies for Odoo Instance Provisioning Module")
    print("=" * 70)
    
    # Required packages
    required_packages = [
        ('psycopg2-binary', 'psycopg2'),  # (install_name, import_name)
        ('requests', 'requests'),
    ]
    
    # Optional packages
    optional_packages = [
        ('docker', 'docker'),
    ]
    
    print("📦 Checking required packages...")
    
    for install_name, import_name in required_packages:
        if check_package(import_name):
            print(f"✅ {install_name} is already installed")
        else:
            print(f"📦 Installing {install_name}...")
            if install_package(install_name):
                print(f"✅ {install_name} installed successfully")
            else:
                print(f"❌ Failed to install {install_name}")
                sys.exit(1)
    
    print("\n📦 Checking optional packages...")
    
    for install_name, import_name in optional_packages:
        if check_package(import_name):
            print(f"✅ {install_name} is already installed")
        else:
            answer = input(f"🤔 Install {install_name}? (y/n): ").lower().strip()
            if answer in ['y', 'yes']:
                print(f"📦 Installing {install_name}...")
                if install_package(install_name):
                    print(f"✅ {install_name} installed successfully")
                else:
                    print(f"⚠️  Failed to install {install_name} (optional)")
            else:
                print(f"⏭️  Skipped {install_name}")
    
    print("\n🎉 Dependencies installation completed!")
    print("\n📋 Next steps:")
    print("1. Restart your Odoo server")
    print("2. Update the app list in Odoo")
    print("3. Install the 'Odoo Instance Provisioning' module")
    print("4. Configure system parameters")
    
    print("\n💡 If you still get import errors:")
    print("- Make sure Odoo is using the same Python environment")
    print("- Check Odoo logs for specific error messages")
    print("- Consider using virtual environments")

if __name__ == "__main__":
    main()
