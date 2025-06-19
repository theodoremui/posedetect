#!/usr/bin/env python3
"""
OpenPose Installation Diagnostic Tool

This script helps diagnose OpenPose installation issues by checking
paths, dependencies, and module availability.
"""

import os
import sys
from pathlib import Path

# Add the src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def check_environment():
    """Check environment variables and basic setup."""
    print("🔍 Checking Environment Variables...")
    
    openpose_path = os.environ.get('OPENPOSEPATH')
    if openpose_path:
        print(f"✅ OPENPOSEPATH is set: {openpose_path}")
        
        if os.path.exists(openpose_path):
            print(f"✅ OPENPOSEPATH directory exists")
        else:
            print(f"❌ OPENPOSEPATH directory does not exist!")
            return False
    else:
        print("❌ OPENPOSEPATH environment variable is not set!")
        print("   Please set OPENPOSEPATH to your OpenPose installation directory")
        return False
    
    return True, openpose_path


def scan_directory_structure(openpose_path):
    """Scan and display OpenPose directory structure."""
    print(f"\n📁 Scanning OpenPose Directory Structure...")
    
    if not os.path.exists(openpose_path):
        print(f"❌ Directory does not exist: {openpose_path}")
        return
    
    # Check main directories
    main_dirs = ['bin', 'lib', 'include', 'models', 'python', 'examples']
    for dir_name in main_dirs:
        dir_path = os.path.join(openpose_path, dir_name)
        if os.path.exists(dir_path):
            print(f"✅ Found {dir_name}/ directory")
        else:
            print(f"⚠️  Missing {dir_name}/ directory")
    
    # Focus on python directory
    python_dir = os.path.join(openpose_path, 'python')
    if os.path.exists(python_dir):
        print(f"\n🐍 Python Directory Contents ({python_dir}):")
        try:
            for item in sorted(os.listdir(python_dir)):
                item_path = os.path.join(python_dir, item)
                if os.path.isdir(item_path):
                    print(f"  📁 {item}/")
                    
                    # Check for openpose subdirectory
                    if item == 'openpose':
                        openpose_subdir = os.path.join(python_dir, 'openpose')
                        print(f"    Contents of openpose/:")
                        try:
                            for subitem in sorted(os.listdir(openpose_subdir)):
                                subitem_path = os.path.join(openpose_subdir, subitem)
                                if os.path.isdir(subitem_path):
                                    print(f"      📁 {subitem}/")
                                    
                                    # Check Release/Debug directories
                                    if subitem in ['Release', 'Debug']:
                                        release_dir = os.path.join(openpose_subdir, subitem)
                                        print(f"        Contents of {subitem}/:")
                                        try:
                                            for file in sorted(os.listdir(release_dir)):
                                                if file.endswith(('.py', '.pyd', '.so')):
                                                    print(f"          🐍 {file}")
                                                else:
                                                    print(f"          📄 {file}")
                                        except PermissionError:
                                            print(f"          ❌ Permission denied")
                                else:
                                    print(f"      📄 {subitem}")
                        except PermissionError:
                            print(f"    ❌ Permission denied")
                else:
                    if item.endswith(('.py', '.pyd', '.so')):
                        print(f"  🐍 {item}")
                    else:
                        print(f"  📄 {item}")
        except PermissionError:
            print(f"  ❌ Permission denied to list directory contents")
    else:
        print(f"❌ Python directory not found: {python_dir}")


def find_openpose_modules(openpose_path):
    """Find all possible OpenPose Python modules."""
    print(f"\n🔍 Searching for OpenPose Python Modules...")
    
    search_paths = [
        os.path.join(openpose_path, 'bin', 'python', 'openpose', 'Release'),
        os.path.join(openpose_path, 'bin', 'python', 'openpose', 'Debug'),
        os.path.join(openpose_path, 'python', 'openpose', 'Release'),
        os.path.join(openpose_path, 'python', 'openpose', 'Debug'),
        os.path.join(openpose_path, 'build', 'python', 'openpose', 'Release'),
        os.path.join(openpose_path, 'build', 'python', 'openpose', 'Debug'),
        os.path.join(openpose_path, 'build', 'python'),
        os.path.join(openpose_path, 'python'),
        os.path.join(openpose_path, 'python', 'dist'),
        os.path.join(openpose_path, 'python', 'openpose'),
        openpose_path,
    ]
    
    module_files = [
        'openpose.py',
        'openpose.pyd',
        'openpose.so',
        '_openpose.pyd',
        '_openpose.so',
        'pyopenpose.py',
        'pyopenpose.pyd',
        'pyopenpose.so',
    ]
    
    found_modules = []
    
    for search_path in search_paths:
        if os.path.exists(search_path):
            print(f"  📁 Checking: {search_path}")
            
            # Check specific module files
            for module_file in module_files:
                module_path = os.path.join(search_path, module_file)
                if os.path.exists(module_path):
                    file_size = os.path.getsize(module_path)
                    print(f"    ✅ Found: {module_file} ({file_size:,} bytes)")
                    found_modules.append(module_path)
            
            # Also scan for any .pyd files (version-specific)
            try:
                for file in os.listdir(search_path):
                    if file.endswith('.pyd') and ('openpose' in file.lower() or 'pyopenpose' in file.lower()):
                        if file not in [os.path.basename(m) for m in found_modules]:
                            module_path = os.path.join(search_path, file)
                            file_size = os.path.getsize(module_path)
                            print(f"    ✅ Found: {file} ({file_size:,} bytes)")
                            found_modules.append(module_path)
            except PermissionError:
                print(f"    ❌ Permission denied to scan directory")
        else:
            print(f"  ❌ Not found: {search_path}")
    
    if found_modules:
        print(f"\n🎉 Found {len(found_modules)} OpenPose module(s):")
        for module in found_modules:
            print(f"  📍 {module}")
    else:
        print(f"\n❌ No OpenPose Python modules found!")
        print("   This indicates that OpenPose was not compiled with Python bindings.")
    
    return found_modules


def test_import_openpose(openpose_path, found_modules):
    """Test importing OpenPose with different path configurations."""
    print(f"\n🧪 Testing OpenPose Import...")
    
    if not found_modules:
        print("❌ No modules found, skipping import test")
        return False
    
    # Test each module location
    for module_path in found_modules:
        module_dir = os.path.dirname(module_path)
        module_name = os.path.basename(module_path).split('.')[0]
        
        print(f"\n  Testing import from: {module_dir}")
        print(f"  Module name: {module_name}")
        
        # Add to Python path temporarily
        if module_dir not in sys.path:
            sys.path.insert(0, module_dir)
        
        try:
            # Try importing
            if module_name in ['openpose', '_openpose']:
                import openpose as op
                print(f"    ✅ Successfully imported 'openpose'")
                
                # Test basic functionality
                try:
                    wrapper = op.WrapperPython()
                    print(f"    ✅ WrapperPython created successfully")
                    return True
                except Exception as e:
                    print(f"    ⚠️  WrapperPython creation failed: {e}")
                    
            elif module_name in ['pyopenpose', '_pyopenpose']:
                import pyopenpose as op
                print(f"    ✅ Successfully imported 'pyopenpose'")
                
                # Test basic functionality
                try:
                    wrapper = op.WrapperPython()
                    print(f"    ✅ WrapperPython created successfully")
                    return True
                except Exception as e:
                    print(f"    ⚠️  WrapperPython creation failed: {e}")
                    
        except ImportError as e:
            print(f"    ❌ Import failed: {e}")
        except Exception as e:
            print(f"    ❌ Unexpected error: {e}")
        finally:
            # Remove from path
            if module_dir in sys.path:
                sys.path.remove(module_dir)
    
    return False


def check_dll_dependencies(openpose_path):
    """Check for OpenPose DLL dependencies on Windows."""
    if not sys.platform.startswith('win'):
        return  # Skip on non-Windows systems
    
    print(f"\n🔧 Checking Windows DLL Dependencies...")
    
    dll_dirs = [
        os.path.join(openpose_path, 'bin'),
        os.path.join(openpose_path, 'build', 'bin'),
        os.path.join(openpose_path, 'build', 'x64', 'Release'),
        os.path.join(openpose_path, 'build', 'x64', 'Debug'),
        os.path.join(openpose_path, 'x64', 'Release'),
        os.path.join(openpose_path, 'x64', 'Debug'),
    ]
    
    found_dll_dirs = []
    for dll_dir in dll_dirs:
        if os.path.exists(dll_dir):
            found_dll_dirs.append(dll_dir)
            print(f"✅ DLL Directory found: {dll_dir}")
            try:
                dll_files = [f for f in os.listdir(dll_dir) if f.endswith('.dll')]
                if dll_files:
                    print(f"   Found {len(dll_files)} DLL files:")
                    # Show important OpenPose DLLs
                    important_dlls = [f for f in dll_files if any(x in f.lower() for x in ['openpose', 'caffe', 'opencv'])]
                    for dll in sorted(important_dlls)[:10]:  # Show first 10 important DLLs
                        dll_path = os.path.join(dll_dir, dll)
                        size = os.path.getsize(dll_path)
                        print(f"     🔧 {dll} ({size:,} bytes)")
                    if len(dll_files) > len(important_dlls):
                        print(f"     ... and {len(dll_files) - len(important_dlls)} other DLL files")
                else:
                    print(f"   ⚠️  No DLL files found")
            except PermissionError:
                print(f"   ❌ Permission denied to list DLL files")
        else:
            print(f"❌ DLL Directory not found: {dll_dir}")
    
    # Check current PATH for OpenPose entries
    print(f"\n🛤️  Checking Windows PATH for OpenPose entries...")
    current_path = os.environ.get('PATH', '')
    path_entries = current_path.split(os.pathsep)
    openpose_entries = [p for p in path_entries if 'openpose' in p.lower()]
    
    if openpose_entries:
        print(f"✅ Found {len(openpose_entries)} OpenPose entries in PATH:")
        for entry in openpose_entries:
            print(f"   📍 {entry}")
    else:
        print(f"⚠️  No OpenPose entries found in current PATH")
        if found_dll_dirs:
            print(f"💡 Suggestion: Add these directories to your PATH:")
            for dll_dir in found_dll_dirs[:2]:  # Show first 2 most likely candidates
                print(f"   {dll_dir}")

def check_dependencies():
    """Check for required dependencies."""
    print(f"\n📦 Checking Python Dependencies...")
    
    required_packages = ['cv2', 'numpy']
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is available")
        except ImportError:
            print(f"❌ {package} is missing - install with: pip install opencv-python numpy")


def provide_solutions(openpose_path, found_modules, import_successful):
    """Provide solutions based on diagnostic results."""
    print(f"\n💡 Recommendations:")
    
    if not import_successful:
        if not found_modules:
            print("""
❌ OpenPose Python bindings not found. To fix this:

1. **Rebuild OpenPose with Python support:**
   - Enable BUILD_PYTHON flag in CMake
   - Ensure Python development headers are installed
   - Rebuild OpenPose from source

2. **Download precompiled version:**
   - Get a precompiled OpenPose build with Python bindings
   - Ensure it matches your Python version and architecture

3. **Check installation guide:**
   - Follow the official OpenPose installation guide
   - Pay special attention to Python binding compilation

4. **Alternative: Use docker:**
   - Consider using a Docker image with OpenPose pre-installed
""")
        else:
            print(f"""
⚠️  OpenPose modules found but import failed. Try:

1. **Manual path setup:**
   Add to your script before importing:
   
   import sys
   sys.path.insert(0, r'{os.path.dirname(found_modules[0])}')
   import openpose

2. **Set PYTHONPATH environment variable:**
   PYTHONPATH={os.path.dirname(found_modules[0])}

3. **Windows DLL PATH issue (most common):**
   Add OpenPose bin directory to your Windows PATH:
   PATH=%PATH%;{openpose_path}\\bin

4. **Check Python version compatibility:**
   Ensure your Python version matches the OpenPose build
   Current Python: {sys.version_info.major}.{sys.version_info.minor}

5. **Check dependencies:**
   The module might need additional DLLs or shared libraries
   - Ensure Visual C++ Redistributable is installed
   - Check that all OpenPose DLLs are present in bin directory
""")
    else:
        print("""
✅ OpenPose appears to be working correctly!

If you're still having issues with the pose detection application:
1. Try running with debug logging: --log-level DEBUG
2. Check file permissions for input files
3. Ensure sufficient disk space for outputs
""")


def main():
    """Main diagnostic function."""
    print("🔧 OpenPose Installation Diagnostic Tool")
    print("=" * 50)
    
    # Check environment
    env_ok, openpose_path = check_environment()
    if not env_ok:
        return 1
    
    # Scan directory structure
    scan_directory_structure(openpose_path)
    
    # Find modules
    found_modules = find_openpose_modules(openpose_path)
    
    # Check DLL dependencies (Windows)
    check_dll_dependencies(openpose_path)
    
    # Test import
    import_successful = test_import_openpose(openpose_path, found_modules)
    
    # Check dependencies
    check_dependencies()
    
    # Provide solutions
    provide_solutions(openpose_path, found_modules, import_successful)
    
    print("\n" + "=" * 50)
    if import_successful:
        print("🎉 Diagnostic completed successfully!")
        return 0
    else:
        print("❌ Issues found - please follow the recommendations above")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 