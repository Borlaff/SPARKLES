#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Sphinx documentation build script for SPARKLES
Provides cross-platform building (works on Windows, macOS, Linux)

Usage:
    python make.py html       # Build HTML documentation
    python make.py clean      # Clean build directory
    python make.py help       # Show all available commands
"""

import os
import sys
import shutil
import argparse
from pathlib import Path

# Get the docs directory
DOCS_DIR = Path(__file__).parent.absolute()
BUILD_DIR = DOCS_DIR / '_build'

def run_sphinx(builder):
    """Run Sphinx with the specified builder"""
    from sphinx.cmd.build import main as sphinx_main
    
    args = [
        '-W',           # Treat warnings as errors
        '--keep-going', # Continue on errors
        '-b', builder,  # Builder to use
        str(DOCS_DIR),      # Source directory
        str(BUILD_DIR / builder),  # Output directory
    ]
    
    return sphinx_main(args)

def clean():
    """Clean build directory"""
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
        print(f"Cleaned: {BUILD_DIR}")
    else:
        print("Build directory not found, nothing to clean")

def build_html():
    """Build HTML documentation"""
    print("Building HTML documentation...")
    result = run_sphinx('html')
    if result == 0:
        html_dir = BUILD_DIR / 'html' / 'index.html'
        print(f"\n✓ HTML built successfully!")
        print(f"View at: {html_dir}")
    return result

def build_epub():
    """Build EPUB e-book"""
    print("Building EPUB documentation...")
    result = run_sphinx('epub')
    if result == 0:
        print("\n✓ EPUB built successfully!")
    return result

def build_pdf():
    """Build PDF documentation (requires LaTeX)"""
    print("Building PDF documentation (requires LaTeX)...")
    # First build LaTeX
    result = run_sphinx('latex')
    if result != 0:
        print("LaTeX build failed")
        return result
    
    # Then convert to PDF
    latex_dir = BUILD_DIR / 'latex'
    print("Converting LaTeX to PDF...")
    try:
        import subprocess
        result = subprocess.run(
            ['make', 'all-pdf'],
            cwd=latex_dir,
            capture_output=True
        )
        if result.returncode == 0:
            print("\n✓ PDF built successfully!")
        return result.returncode
    except Exception as e:
        print(f"Error building PDF: {e}")
        return 1

def linkcheck():
    """Check for broken links"""
    print("Checking for broken links...")
    result = run_sphinx('linkcheck')
    return result

def show_help():
    """Show available commands"""
    print("""
Sphinx Documentation Build Script for SPARKLES

Usage: python make.py <command>

Available Commands:
    html        Build HTML documentation (default)
    clean       Clean build directory
    epub        Build EPUB e-book
    pdf         Build PDF documentation (requires LaTeX)
    linkcheck   Check for broken links
    help        Show this help message

Examples:
    python make.py html
    python make.py clean && python make.py html
    python make.py linkcheck
    """)

def main():
    parser = argparse.ArgumentParser(
        description='Sphinx documentation build script for SPARKLES',
        prog='make.py'
    )
    
    parser.add_argument(
        'command',
        nargs='?',
        default='html',
        help='Build command (html, clean, epub, pdf, linkcheck, help)'
    )
    
    args = parser.parse_args()
    command = args.command.lower()
    
    commands = {
        'html': build_html,
        'clean': clean,
        'epub': build_epub,
        'pdf': build_pdf,
        'linkcheck': linkcheck,
        'help': show_help,
    }
    
    if command not in commands:
        print(f"Unknown command: {command}")
        show_help()
        sys.exit(1)
    
    try:
        result = commands[command]()
        sys.exit(result if isinstance(result, int) else 0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
