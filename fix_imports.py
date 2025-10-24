"""
Fix all import paths in the OSS repository.

Updates imports from old production paths to new OSS paths:
- config. → verityngn.config.
- models. → verityngn.models.
- services. → verityngn.services.
- agents. → verityngn.
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(filepath):
    """Fix import paths in a single file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Fix patterns
    replacements = [
        # config imports
        (r'^from config\.', 'from verityngn.config.'),
        (r'^import config\.', 'import verityngn.config.'),
        
        # models imports
        (r'^from models\.', 'from verityngn.models.'),
        (r'^import models\.', 'import verityngn.models.'),
        
        # services imports (but not from within services/)
        (r'^from services\.', 'from verityngn.services.'),
        (r'^import services\.', 'import verityngn.services.'),
        
        # agents imports
        (r'^from agents\.', 'from verityngn.'),
        (r'^import agents\.', 'import verityngn.'),
        
        # utils imports
        (r'^from utils\.', 'from verityngn.utils.'),
        (r'^import utils\.', 'import verityngn.utils.'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # Special case: relative imports within verityngn/ can stay as-is or be made absolute
    # But we need to check if file is in services/, then services. imports should be relative
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Fix all Python files in verityngn/."""
    repo_root = Path(__file__).parent
    verityngn_dir = repo_root / 'verityngn'
    
    if not verityngn_dir.exists():
        print(f"Error: {verityngn_dir} not found")
        return
    
    print("🔧 Fixing import paths in OSS repository...")
    print()
    
    fixed_count = 0
    total_count = 0
    
    for filepath in verityngn_dir.rglob('*.py'):
        total_count += 1
        if fix_imports_in_file(filepath):
            fixed_count += 1
            rel_path = filepath.relative_to(repo_root)
            print(f"✅ Fixed: {rel_path}")
    
    print()
    print(f"📊 Summary: Fixed {fixed_count}/{total_count} files")
    
    if fixed_count > 0:
        print("\n✨ Import paths updated successfully!")
    else:
        print("\n✅ No fixes needed - all imports already correct")

if __name__ == '__main__':
    main()


