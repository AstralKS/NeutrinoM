"""Test the token optimizer."""

from advisor.analysis import TokenOptimizer

# Test code with various bloat
test_files = {
    "test.py": """
# Auto-generated file
# Created by: Some Tool
# Date: 2024-01-01
import os
import sys
import json
from typing import List, Dict, Optional

# TODO: Fix this later
# FIXME: This is broken
class MyClass:
    def method(self):
        # Some comment
        # Another comment
        # Yet another
        pass




        
    def another(self):
        return True
""",
    "test.tsx": """
import React from 'react';
import { useState, useEffect } from 'react';
// eslint-disable-next-line
// @ts-ignore
// prettier-ignore
export function Component() {
    return <div>Hello</div>;
}
""",
}

optimizer = TokenOptimizer()
optimized, stats = optimizer.optimize(test_files)

print(f"Original: {stats.original_chars} chars")
print(f"Compressed: {stats.compressed_chars} chars")
print(f"Savings: {stats.savings_percent:.1f}%")
print(f"Files: {stats.files_processed}")
print()
print("=== Optimized Python ===")
print(optimized.get("test.py", "N/A"))
print()
print("=== Optimized TSX ===")
print(optimized.get("test.tsx", "N/A"))
