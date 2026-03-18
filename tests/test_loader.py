def test_loadData():
    from loader import loadData

    # Arrange
    path = "tests//testdata//light_bulb.jani"

    # Act
    data = loadData(path)

    # Assert
    assert data["name"] == "light_bulb"
