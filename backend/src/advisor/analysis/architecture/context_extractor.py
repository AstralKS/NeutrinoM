"""Context extractor - file categorization, imports, and token estimation."""

import ast
import logging
import re

from .models import (
    AnalysisBatch,
    FileCategory,
    BACKEND_TOKEN_THRESHOLD,
    FRONTEND_TOKEN_THRESHOLD,
    SMALL_APP_THRESHOLD,
)

logger = logging.getLogger(__name__)


class ContextExtractor:
    """Pure parsing operations - AST, regex, token counting."""

    def __init__(self, model_name: str = "gpt-4o"):
        self._model_name = model_name

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count using tiktoken or char/4 fallback."""
        try:
            import tiktoken
            return len(tiktoken.encoding_for_model(self._model_name).encode(text))
        except Exception:
            return len(text) // 4

    def categorize_files(self, file_contents: dict[str, str]) -> dict[FileCategory, dict[str, str]]:
        """Categorize files into Frontend, Backend, or Infra."""
        frontend_exts = {".js", ".ts", ".jsx", ".tsx", ".vue", ".css", ".scss", ".sass", ".less"}
        infra_files = {"dockerfile", "docker-compose.yml", "docker-compose.yaml", "nginx.conf"}
        infra_exts = {".tf", ".tfvars", ".hcl"}
        backend_exts = {".py", ".go", ".java", ".rs", ".rb", ".php", ".cs"}
        frontend_paths = {"src/client", "public/", "frontend/", "web/", "client/", "ui/"}
        infra_paths = {"docker/", "k8s/", "kubernetes/", "terraform/", "infra/", ".github/"}

        categorized = {FileCategory.FRONTEND: {}, FileCategory.BACKEND: {}, FileCategory.INFRA: {}}

        for path, content in file_contents.items():
            path_lower = path.lower().replace("\\", "/")
            basename = path_lower.split("/")[-1]
            ext = "." + basename.split(".")[-1] if "." in basename else ""

            if basename in infra_files or ext in infra_exts or any(p in path_lower for p in infra_paths):
                categorized[FileCategory.INFRA][path] = content
            elif ext in frontend_exts or any(p in path_lower for p in frontend_paths):
                categorized[FileCategory.FRONTEND][path] = content
            else:
                categorized[FileCategory.BACKEND][path] = content

        return categorized

    def extract_imports(self, content: str, file_path: str) -> list[str]:
        """Extract imports using AST for Python, regex for JS/TS."""
        if file_path.endswith(".py"):
            return self._extract_python_imports(content)
        return self._extract_js_imports(content)

    def _extract_python_imports(self, content: str) -> list[str]:
        """Extract Python imports using AST."""
        try:
            tree = ast.parse(content)
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)
            return imports
        except SyntaxError:
            # Fallback to regex
            imports = []
            for line in content.split("\n"):
                if m := re.match(r'^(?:from|import)\s+([\w.]+)', line.strip()):
                    imports.append(m.group(1))
            return imports

    def _extract_js_imports(self, content: str) -> list[str]:
        """Extract JS/TS imports using regex."""
        patterns = [
            r'import\s+.*\s+from\s+["\']([^"\']+)["\']',
            r'require\s*\(["\']([^"\']+)["\']\)',
        ]
        imports = []
        for pattern in patterns:
            imports.extend(m.group(1) for m in re.finditer(pattern, content))
        return imports

    def prepare_batches(self, categorized: dict[FileCategory, dict[str, str]]) -> list[AnalysisBatch]:
        """Prepare LLM API call batches based on token thresholds."""
        be_files, fe_files = categorized.get(FileCategory.BACKEND, {}), categorized.get(FileCategory.FRONTEND, {})
        infra_files = categorized.get(FileCategory.INFRA, {})

        be_ctx = self._extract_backend_context(be_files)
        fe_ctx = self._extract_frontend_context(fe_files)
        infra_ctx = self._extract_infra_context(infra_files)

        be_tok, fe_tok = self.estimate_tokens(be_ctx), self.estimate_tokens(fe_ctx)
        infra_tok = self.estimate_tokens(infra_ctx)

        def batch(cat, files, tok, ctx):
            return AnalysisBatch(category=cat, files=files, token_count=tok, extracted_context=ctx)

        if be_tok + fe_tok + infra_tok < SMALL_APP_THRESHOLD:
            return [batch("Full Codebase", {**be_files, **fe_files, **infra_files},
                         be_tok + fe_tok + infra_tok, "\n\n".join(filter(None, [be_ctx, fe_ctx, infra_ctx])))]

        batches = []
        if be_ctx:
            batches.append(batch("Backend", be_files, be_tok, be_ctx))
        if fe_tok > FRONTEND_TOKEN_THRESHOLD:
            if fe_ctx:
                batches.append(batch("Frontend", fe_files, fe_tok, fe_ctx))
            if infra_ctx:
                batches.append(batch("Infrastructure", infra_files, infra_tok, infra_ctx))
        elif fe_ctx or infra_ctx:
            batches.append(batch("Frontend + Infrastructure", {**fe_files, **infra_files},
                                fe_tok + infra_tok, "\n\n".join(filter(None, [fe_ctx, infra_ctx]))))
        return batches

    def _extract_frontend_context(self, files: dict[str, str]) -> str:
        """Lightweight extraction: imports + signatures only."""
        if not files:
            return ""
        parts = ["=== FRONTEND FILES ==="]
        for path, content in files.items():
            parts.append(f"\n--- {path} ---")
            if imports := self.extract_imports(content, path):
                parts.append(f"Imports: {', '.join(imports[:10])}")
            sigs = []
            for m in re.finditer(r'(?:function|class)\s+(\w+)', content):
                sigs.append(m.group(1))
            for m in re.finditer(r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>', content):
                sigs.append(m.group(1))
            if sigs:
                parts.append(f"Exports: {', '.join(sigs[:15])}")
        return "\n".join(parts)

    def _extract_backend_context(self, files: dict[str, str]) -> str:
        """Deep extraction: imports + docstrings + signatures."""
        if not files:
            return ""
        parts = ["=== BACKEND FILES ==="]
        for path, content in files.items():
            parts.append(f"\n--- {path} ---")
            if path.endswith(".py"):
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)][:5]
                            parts.append(f"class {node.name}: [{', '.join(methods)}]")
                        elif isinstance(node, ast.FunctionDef):
                            args = [a.arg for a in node.args.args][:5]
                            parts.append(f"def {node.name}({', '.join(args)})")
                except SyntaxError:
                    pass
            else:
                for m in re.finditer(r'(?:function|class)\s+(\w+)', content):
                    parts.append(m.group(0))
        return "\n".join(parts)

    def _extract_infra_context(self, files: dict[str, str]) -> str:
        """Minimal extraction: key config values only."""
        if not files:
            return ""
        parts = ["=== INFRA FILES ==="]
        for path, content in files.items():
            basename = path.split("/")[-1].split("\\")[-1].lower()
            parts.append(f"\n--- {path} ---")
            if "dockerfile" in basename:
                if m := re.search(r'^FROM\s+(.+)$', content, re.MULTILINE):
                    parts.append(f"Base: {m.group(1)}")
            elif basename.endswith((".yaml", ".yml")):
                keys = re.findall(r'^(\w+):', content, re.MULTILINE)[:10]
                if keys:
                    parts.append(f"Keys: {', '.join(keys)}")
            elif basename.endswith(".tf"):
                resources = set(re.findall(r'resource\s+"(\w+)"', content))
                if resources:
                    parts.append(f"Resources: {', '.join(resources)}")
        return "\n".join(parts)
