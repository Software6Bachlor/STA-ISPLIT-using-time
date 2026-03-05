## Naming Convention
```python
def test<Function><Scenario>():
    """Clear description of what's being tested"""
```
Examples:
- test_UserLoginWithInvalidPassword()
- test_CalculateDiscountRaisesErrorForNegativeValues()

## AAA Pattern (Arrange-Act-Assert)
```python
def testCalculateTotal():
    # Arrange - Set up test data
    items = [10, 20, 30]

    # Act - Execute the function
    result = calculate_total(items)

    # Assert - Verify the result
    assert result == 60
```

## Use Fixtures for Setup
```python
# conftest.py
@pytest.fixture
def sampleUser():
    return User(name="John", email="john@example.com")

# test_users.py
def testUserEmail(sample_user):
    assert sample_user.email == "john@example.com"
```
## Parametrize Similar Tests
```python
@pytest.mark.parametrize("input,expected", [
    (5, 25),
    (0, 0),
    (-3, 9),
])
def testSquare(input, expected):
    assert square(input) == expected
```
## Test Exceptions
```python
def testDivideByZero():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0)
```
