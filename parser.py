from models.STA import Model

def parse_model(data: dict) -> Model:
    model = Model(
        name=data.get("name", ""),
        jani_version=data.get("jani_version", ""),
        type=data.get("type", "")
    )
    model.variables = data.get("variables", [])
    model.constants = data.get("constants", [])
    return model