"""Test script for DebtPrioritizer with linters."""

import sys
sys.path.insert(0, ".")

from advisor.analysis.analyzers.debt_prioritizer import DebtPrioritizer

# Sample file contents with intentional issues
test_files = {
    "app.py": """
import os
api_key = "sk-secret-12345"
password = "admin123"

def process(data):
    pass

try:
    risky_operation()
except:
    pass
""",
    "utils.py": """
import subprocess

def run_cmd(cmd):
    subprocess.call(cmd, shell=True)

def sql_query(user_input):
    query = "SELECT * FROM users WHERE id = " + user_input
    execute(query)
""",
    "main.py": """
def calculate(x, y):
    return x + y
"""
}

print("Running DebtPrioritizer test...")
print("=" * 60)

prioritizer = DebtPrioritizer()
results = prioritizer.prioritize(test_files, [], None)

print(f"\nFound {len(results)} debt items:\n")
for i, item in enumerate(results, 1):
    print(f"{i}. [{item.severity.upper()}] {item.title}")
    print(f"   Category: {item.category}")
    print(f"   Priority Score: {item.priority_score}")
    desc = item.description[:100] + "..." if len(item.description) > 100 else item.description
    print(f"   Description: {desc}")
    if item.evidence:
        print(f"   Evidence: {item.evidence}")
    print()
