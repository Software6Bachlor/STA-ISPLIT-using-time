from models.STA import Model
from parser import parseModel
from loader import loadData

model_1: Model = parseModel(loadData("tests//testdata//ModestSTA.jani") )
