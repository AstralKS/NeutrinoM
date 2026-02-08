"""Test script for DeepArchitectureAnalyzer with Hybrid AST + LLM."""

import sys
sys.path.insert(0, ".")

from advisor.analysis.analyzers.architecture_deep import (
    DeepArchitectureAnalyzer,
    DeepArchitectureAnalysis,
)

# Sample file contents simulating a layered architecture
test_files = {
    "src/main.py": """
from src.api.routes import create_app
from src.config import settings

app = create_app()

if __name__ == "__main__":
    app.run(host=settings.HOST, port=settings.PORT)
""",
    "src/api/routes.py": """
from flask import Flask, jsonify
from src.services.user_service import UserService
from src.services.order_service import OrderService

def create_app():
    app = Flask(__name__)
    user_service = UserService()
    order_service = OrderService()
    
    @app.route('/users')
    def get_users():
        return jsonify(user_service.get_all())
    
    @app.route('/orders')
    def get_orders():
        return jsonify(order_service.get_all())
    
    return app
""",
    "src/services/user_service.py": """
from src.repositories.user_repository import UserRepository
from src.utils.cache import cache_result

class UserService:
    def __init__(self):
        self.repo = UserRepository()
    
    @cache_result(ttl=300)
    def get_all(self):
        return self.repo.find_all()
    
    def get_by_id(self, user_id: int):
        return self.repo.find_by_id(user_id)
""",
    "src/services/order_service.py": """
from src.repositories.order_repository import OrderRepository
from src.services.user_service import UserService

class OrderService:
    def __init__(self):
        self.repo = OrderRepository()
        self.user_service = UserService()
    
    def get_all(self):
        return self.repo.find_all()
    
    def create_order(self, user_id: int, items: list):
        user = self.user_service.get_by_id(user_id)
        return self.repo.create(user_id=user_id, items=items)
""",
    "src/repositories/user_repository.py": """
from src.database.connection import get_db
from src.models.user import User

class UserRepository:
    def __init__(self):
        self.db = get_db()
    
    def find_all(self):
        return self.db.query(User).all()
    
    def find_by_id(self, user_id: int):
        return self.db.query(User).filter(User.id == user_id).first()
""",
    "src/repositories/order_repository.py": """
from src.database.connection import get_db
from src.models.order import Order

class OrderRepository:
    def __init__(self):
        self.db = get_db()
    
    def find_all(self):
        return self.db.query(Order).all()
    
    def create(self, user_id: int, items: list):
        order = Order(user_id=user_id, items=items)
        self.db.add(order)
        return order
""",
    "src/utils/cache.py": """
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379)

def cache_result(ttl=60):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{args}:{kwargs}"
            cached = redis_client.get(key)
            if cached:
                return cached
            result = func(*args, **kwargs)
            redis_client.setex(key, ttl, result)
            return result
        return wrapper
    return decorator
""",
    "src/config.py": """
import os

class Settings:
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

settings = Settings()
""",
}

print("=" * 70)
print("Testing DeepArchitectureAnalyzer (Hybrid AST + LLM)")
print("=" * 70)

analyzer = DeepArchitectureAnalyzer()
result = analyzer.analyze(test_files, None)

print("\n[1] DEPENDENCY GRAPH")
print("-" * 50)
for path, node in result.dependency_graph.items():
    if node.imports:
        print(f"  {path}")
        print(f"    imports: {node.imports[:5]}")
        if node.imported_by:
            print(f"    imported_by: {node.imported_by}")

print("\n[2] ARCHITECTURE TYPE")
print("-" * 50)
print(f"  {result.architecture_type}")

print("\n[3] ENTRY POINTS")
print("-" * 50)
for ep in result.entry_points:
    print(f"  - {ep}")

print("\n[4] SHARED UTILITIES")
print("-" * 50)
for util in result.shared_utilities:
    print(f"  - {util}")

print("\n[5] CIRCULAR DEPENDENCIES")
print("-" * 50)
if result.circular_dependencies:
    for a, b in result.circular_dependencies:
        print(f"  [!] {a} <-> {b}")
else:
    print("  None detected [OK]")

print("\n[6] COUPLING SCORE")
print("-" * 50)
print(f"  {result.coupling_score:.2f} (0=loose, 1=tight)")

print("\n[7] CACHE PATTERNS")
print("-" * 50)
for cp in result.cache_patterns:
    print(f"  - {cp.type} ({cp.location})")

print("\n[8] STATE PATTERNS")
print("-" * 50)
if result.state_patterns:
    for sp in result.state_patterns:
        print(f"  - {sp.pattern} ({sp.complexity})")
else:
    print("  None detected")

print("\n[9] MERMAID DIAGRAM")
print("-" * 50)
if result.mermaid_diagram:
    print(result.mermaid_diagram[:500])
    if len(result.mermaid_diagram) > 500:
        print("  ... [truncated]")
else:
    print("  No diagram generated")

print("\n" + "=" * 70)
print("Test completed!")
print("=" * 70)
