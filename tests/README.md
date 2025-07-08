# Tests for Slack AI App

This directory contains tests for the Slack AI App. The tests are organized to mirror the structure of the application code.

## Test Structure

- `tests/api/`: Tests for API routes
- `tests/use_cases/`: Tests for use cases
- `tests/integrations/`: Tests for integrations with external services
- `tests/config/`: Tests for configuration

## Running Tests

To run the tests, use the following command from the project root:

```bash
pytest
```

To run tests with coverage:

```bash
pytest --cov=app
```

To run a specific test file:

```bash
pytest tests/path/to/test_file.py
```

## Test Fixtures

Common test fixtures are defined in `tests/conftest.py`. These include:

- `mock_conversation_repo`: Mock for the conversation repository
- `mock_llm_chat`: Mock for the LLM chat interface
- `mock_slack_client`: Mock for the Slack client
- `mock_web_client`: Mock for the Slack WebClient
- `sample_conversation`: Sample conversation data
- `sample_slack_event`: Sample Slack event data
- `sample_slack_threaded_event`: Sample threaded Slack event data

## Writing Tests

When writing new tests:

1. Follow the existing pattern of using pytest fixtures for dependencies
2. Use the Arrange-Act-Assert pattern for test structure
3. Mock external dependencies to isolate the code being tested
4. Test both success and error cases
5. Add appropriate docstrings to describe what each test is checking

## Test Coverage

The tests aim to cover:

- API routes and request handling
- Use case business logic
- Integration with external services
- Error handling and edge cases

## Continuous Integration

These tests are designed to be run as part of a CI/CD pipeline to ensure code quality and prevent regressions.
