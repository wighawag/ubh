import sys

def getServices(servicesList):
    dict = {}
    for moduleName in servicesList:
        __import__(moduleName)
        module = sys.modules[moduleName]
        for attributeName, attribute in module.__dict__.items():
            if attributeName[0] != '_' and hasattr(attribute, '__call__'):
                dict[moduleName + '.' + attributeName] = attribute
    return dict
