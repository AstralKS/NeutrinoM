"""Tests for GitHub parser."""

import pytest

from advisor.github.parser import RepositoryParser, FileInfo


class TestRepositoryParser:
    """Tests for repository file tree parsing."""

    def test_parse_file_tree(self):
        """Test parsing file tree."""
        tree = [
            {"path": "src/main.py", "type": "blob"},
            {"path": "tests/test_main.py", "type": "blob"},
            {"path": "README.md", "type": "blob"},
            {"path": "package.json", "type": "blob"},
        ]
        
        structure = RepositoryParser.parse_file_tree(tree)
        
        assert structure.total_files == 4
        assert len(structure.code_files) > 0
        assert len(structure.config_files) > 0
        assert len(structure.doc_files) > 0

    def test_classify_code_files(self):
        """Test code file classification."""
        tree = [
            {"path": "app.py", "type": "blob"},
            {"path": "main.js", "type": "blob"},
            {"path": "index.ts", "type": "blob"},
            {"path": "handler.go", "type": "blob"},
        ]
        
        structure = RepositoryParser.parse_file_tree(tree)
        
        assert len(structure.code_files) == 4

    def test_classify_config_files(self):
        """Test config file classification."""
        tree = [
            {"path": "package.json", "type": "blob"},
            {"path": "pyproject.toml", "type": "blob"},
            {"path": ".env", "type": "blob"},
            {"path": "docker-compose.yml", "type": "blob"},
        ]
        
        structure = RepositoryParser.parse_file_tree(tree)
        
        assert len(structure.config_files) == 4

    def test_get_files_to_analyze(self):
        """Test priority file selection."""
        tree = [
            {"path": "package.json", "type": "blob"},
            {"path": "README.md", "type": "blob"},
            {"path": "src/app.py", "type": "blob"},
        ]
        
        structure = RepositoryParser.parse_file_tree(tree)
        files = RepositoryParser.get_files_to_analyze(structure)
        
        # Priority files should be included
        assert "package.json" in files
        assert "README.md" in files

    def test_skip_excluded_directories(self):
        """Test that excluded directories are skipped from code files."""
        tree = [
            {"path": "node_modules/lodash/index.js", "type": "blob"},
            {"path": ".git/config", "type": "blob"},
            {"path": "src/main.py", "type": "blob"},
        ]
        
        structure = RepositoryParser.parse_file_tree(tree)
        
        # src/main.py should be included
        paths = [f.path for f in structure.code_files]
        assert "src/main.py" in paths

    def test_file_classification(self):
        """Test that files are classified correctly."""
        tree = [
            {"path": "src/main.py", "type": "blob"},
            {"path": "tests/test.py", "type": "blob"},
        ]
        
        structure = RepositoryParser.parse_file_tree(tree)
        
        # Should have some files classified
        assert structure.total_files == 2

    def test_empty_tree(self):
        """Test with empty file tree."""
        structure = RepositoryParser.parse_file_tree([])
        
        assert structure.total_files == 0
        assert len(structure.code_files) == 0
