def testBasicExample():
    """A simple test to verify pytest is working"""
    result = 2 + 2
    assert result == 4

def testStringOperations():
    """Test string manipulation"""
    text = "hello"
    assert text.upper() == "HELLO"
    assert len(text) == 5
