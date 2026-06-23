from rdflib import Graph, URIRef, Literal, RDF
from pandas import read_csv
import pandas as pd

class Handler():
    def __init__(self):
        self.dbPathOrUrl = ""

    # Methods
    def getDbPAthOrUrl(self):
        return self.dbPathOrUrl 
     # it returns the path or URL of the database
    
    def setDbPathOrUrl(self, pathOrUrl: str):
        self.dbPathOrUrl = pathOrUrl
        return True
     # it enables to set a new path or URL for 
     # the database to handle

class UploadHandler(Handler):
    def __init__(self):
        super().__init__()

    # Methods
    def pushDataToDb(self, path: str): 
        pass






