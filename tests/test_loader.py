def test_load_data():
    from loader import load_data
    
    # Arrange
    path = "tests//testdata//light_bulb.jani"

    # Act
    data = load_data(path)

    # Assert
    assert data["name"] == "light_bulb"