#!/usr/bin/env python3
import os
import sys
from pathlib import Path

def get_file_extension(filename):
    """Get file extension for syntax highlighting in markdown"""
    ext = Path(filename).suffix.lower()
    extension_map = {
        '.js': 'javascript',
        '.html': 'html',
    }
    return extension_map.get(ext, 'text')

def should_skip_file(file_path, script_name):
    """Check if file should be skipped"""
    filename = os.path.basename(file_path)
    
    # Skip the script itself
    if filename == script_name:
        return True
    
    # Skip output file
    if filename == 'myProj.txt':
        return True
    
    # Skip common binary and cache files
    skip_extensions = {
        '.pyd', '.css', '.svg', '.ico', '.png', '.webmanifest'
    }
    
    # Skip common directories
    skip_dirs = {
        '__pycache__','node_modules','data', 'dist', 'modals'
    }
    
    file_ext = Path(file_path).suffix.lower()
    if file_ext in skip_extensions:
        return True
    
    # Check if any part of the path contains skip directories
    path_parts = Path(file_path).parts
    if any(part in skip_dirs for part in path_parts):
        return True
    
    return False

def read_file_content(file_path):
    """Read file content with multiple encoding attempts"""
    encodings = ['utf-8', 'latin-1', 'cp1252', 'ascii']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except Exception:
            break
    
    # If all encodings fail, try reading as binary and represent as hex
    try:
        with open(file_path, 'rb') as f:
            binary_content = f.read()
            if len(binary_content) > 1024:  # Limit binary output
                return f"[Binary file - first 1024 bytes as hex]\n{binary_content[:1024].hex()}"
            else:
                return f"[Binary file as hex]\n{binary_content.hex()}"
    except Exception as e:
        return f"[Error reading file: {str(e)}]"

def traverse_and_extract():
    """Main function to traverse files and extract contents"""
    script_name = os.path.basename(sys.argv[0])
    current_dir = os.getcwd()
    output_file = 'myProj.txt'
    
    print(f"Starting file extraction in: {current_dir}")
    print(f"Output will be saved to: {output_file}")
    print("-" * 50)
    
    with open(output_file, 'w', encoding='utf-8') as output:
        output.write(f"# My Project\n")
        
        file_count = 0
        
        # Walk through all files and directories
        for root, dirs, files in os.walk(current_dir):
            # Sort for consistent output
            dirs.sort()
            files.sort()
            
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, current_dir)
                
                if should_skip_file(file_path, script_name):
                    print(f"Skipping: {relative_path}")
                    continue
                
                print(f"Processing: {relative_path}")
                
                try:
                    content = read_file_content(file_path)
                    file_ext = get_file_extension(file)
                    
                    output.write(f"### `{relative_path}`\n")
                    output.write(f"```{file_ext}\n")
                    output.write(content)
                    if not content.endswith('\n'):
                        output.write('\n')
                    output.write("```\n\n")
                    
                    file_count += 1
                    
                except Exception as e:
                    print(f"Error processing {relative_path}: {str(e)}")
                    output.write(f"### `{relative_path}`\n")
                    output.write(f"```text\n")
                    output.write(f"[Error reading file: {str(e)}]\n")
                    output.write("```\n\n")
    
    print("-" * 50)
    print(f"Extraction complete! Processed {file_count} files.")
    print(f"Results saved to: {output_file}")

if __name__ == "__main__":
    traverse_and_extract()
