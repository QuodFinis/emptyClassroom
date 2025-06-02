"""
Tests for the classrooms app.

This file imports and re-exports the test classes from the tests directory
to maintain backward compatibility with any code that might be importing
the test classes from tests.py.
"""

from django.test import TestCase

# Import test classes from the tests directory
from classrooms.tests.test_login import LoginTestCase
from classrooms.tests.test_password_reset import PasswordResetTestCase
from classrooms.tests.test_integration import IntegrationTestCase

# Re-export the test classes
__all__ = ['LoginTestCase', 'PasswordResetTestCase', 'IntegrationTestCase']
