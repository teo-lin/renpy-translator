"""
Root conftest.py for pytest configuration

Disables output capture to avoid Windows I/O errors during test discovery
"""

import pytest


def pytest_configure(config):
    """Configure pytest to avoid Windows I/O errors"""
    # Disable output capture to prevent I/O errors on Windows
    config.option.capture = 'no'

    # Add custom markers
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "e2e: mark test as an end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """Auto-add markers based on test file names"""
    for item in items:
        if "test_unit_" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "test_int_" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "test_e2e_" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)
