"""Test the DeepReviewOrchestrator with mock data."""

import asyncio
import logging
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from advisor.analysis.core.deep_review import DeepReviewOrchestrator

# configure logging
logging.basicConfig(level=logging.INFO)

async def main():
    orchestrator = DeepReviewOrchestrator()
    
    # Mock file contents
    files = {
        "src/app/page.tsx": """
import React from 'react';
import { Header } from '@/components/Header';

export default function Home() {
  return (
    <main>
      <Header />
      <h1>Welcome to Neutrino</h1>
    </main>
  );
}
""",
        "src/api/routes.py": """
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class User(BaseModel):
    name: str

@app.get("/users")
def get_users():
    # TODO: Implement database info
    return [{"name": "John"}]
""",
        "Dockerfile": """
FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["uvicorn", "main:app"]
""",
        "requirements.txt": """
fastapi==0.95.0
uvicorn==0.21.1
""",
        "package.json": """
{
  "name": "frontend",
  "dependencies": {
    "react": "^18.2.0",
    "next": "13.4.0"
  }
}
"""
    }

    print("Starting deep review test...")
    result = await orchestrator.review("owner/repo", files)
    
    print("\n=== TECHNICAL SUMMARY ===")
    print(result.aggregated_technical[:200] + "...")
    
    print("\n=== EXECUTIVE SUMMARY ===")
    print(result.aggregated_executive[:200] + "...")
    
    print("\n=== STATS ===")
    print(f"Total Tokens: {result.total_tokens}")
    if result.compression_stats:
        print(f"Compression: {result.compression_stats.savings_percent:.1f}% saved")

if __name__ == "__main__":
    asyncio.run(main())
