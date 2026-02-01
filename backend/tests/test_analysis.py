"""Tests for stack detection."""

from advisor.analysis.stack_detector import StackDetector


def test_detect_languages(sample_file_tree):
    """Test language detection from file extensions."""
    detector = StackDetector()
    result = detector.detect(sample_file_tree, {})

    assert "TypeScript" in result.languages or "TypeScript (React)" in result.languages


def test_detect_frameworks(sample_file_contents):
    """Test framework detection from package.json."""
    detector = StackDetector()
    result = detector.detect([], sample_file_contents)

    assert "React" in result.frameworks
    assert "Next.js" in result.frameworks


def test_detect_tools(sample_file_tree, sample_file_contents):
    """Test tool detection from file tree."""
    detector = StackDetector()
    result = detector.detect(sample_file_tree, sample_file_contents)

    assert "Docker" in result.tools
    assert "GitHub Actions" in result.tools


def test_extract_versions(sample_file_contents):
    """Test version extraction from package.json."""
    detector = StackDetector()
    result = detector.detect([], sample_file_contents)

    assert "react" in result.versions or "project" in result.versions


def test_empty_input():
    """Test handling of empty input."""
    detector = StackDetector()
    result = detector.detect([], {})

    assert result.languages == []
    assert result.frameworks == []
