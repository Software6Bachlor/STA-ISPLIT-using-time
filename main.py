from loader import loadData, retrieveModelNames, selectModels
from parser import parseModel

def main():
    """Main entry point"""
    print("STA-ISPLIT Project")

    models = retrieveModelNames()
    userInput = selectModels(models)

    data = loadData(userInput)
    model = parseModel(data)
    print(model)


if __name__ == "__main__":
    main()
