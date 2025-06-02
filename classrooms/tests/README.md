# Login Tests Documentation

This document provides an overview of the tests implemented for the login functionality in the Empty Classrooms application.

## Test Structure

The tests are organized into three main classes:

1. `LoginTestCase` - Tests for the core login functionality
2. `PasswordResetTestCase` - Tests for the password reset functionality
3. `IntegrationTestCase` - Integration tests for login with other parts of the application

## Test Coverage

### LoginTestCase

- `test_login_page_loads_correctly`: Verifies that the login page loads with a 200 status code and contains the expected form.
- `test_login_successful`: Tests that a user can successfully log in with valid credentials.
- `test_login_with_invalid_credentials`: Tests that login fails with invalid credentials.
- `test_login_with_inactive_user`: Tests that login with an inactive user redirects to resend verification.
- `test_already_authenticated_user_redirected`: Tests that an already authenticated user is redirected to the index page.
- `test_csrf_token_present`: Tests that the CSRF token is present in the login form.
- `test_login_form_validation`: Tests form validation for empty fields.
- `test_login_maintains_session`: Tests that login creates and maintains a session.

### PasswordResetTestCase

- `test_forgot_password_page_loads`: Tests that the forgot password page loads correctly.
- `test_forgot_password_valid_email`: Tests that submitting a valid email sends a password reset email.
- `test_forgot_password_invalid_email`: Tests that submitting an invalid email shows an error message.

### IntegrationTestCase

- `test_login_required_for_profile`: Tests that the profile page requires login.
- `test_login_required_for_bookings`: Tests that the bookings page requires login.
- `test_login_logout_flow`: Tests the complete login-logout flow.

## Running the Tests

To run all the tests:

```bash
python manage.py test classrooms.tests
```

To run a specific test class:

```bash
python manage.py test classrooms.tests.LoginTestCase
python manage.py test classrooms.tests.PasswordResetTestCase
python manage.py test classrooms.tests.IntegrationTestCase
```

To run a specific test method:

```bash
python manage.py test classrooms.tests.LoginTestCase.test_login_successful
```

## Test Environment

The tests use Django's built-in testing framework and include:

- `Client` for simulating HTTP requests
- `TestCase` for database setup and teardown
- `override_settings` for temporarily modifying settings during tests
- Django's authentication system for user creation and login
- Django's messaging framework for testing messages
- Django's email testing utilities for testing email sending

## Best Practices Implemented

1. **Isolation**: Each test is isolated and doesn't depend on the state from other tests.
2. **Setup/Teardown**: Common setup code is in the `setUp` method to avoid repetition.
3. **Comprehensive Coverage**: Tests cover both successful and error cases.
4. **Security Testing**: Tests for CSRF protection and authentication requirements.
5. **Integration Testing**: Tests how login integrates with other parts of the application.
6. **Clear Naming**: Test methods have descriptive names that explain what they test.
7. **Documentation**: Each test method has a docstring explaining its purpose.

## Extending the Tests

When adding new features to the login functionality, corresponding tests should be added to maintain test coverage. Follow these guidelines:

1. Add tests for both successful and error cases
2. Test edge cases and boundary conditions
3. Follow the naming convention: `test_<functionality>_<scenario>`
4. Add appropriate docstrings to explain the purpose of each test
5. Update this documentation to reflect the new tests