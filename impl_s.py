# Importo cose necessarie
import json
import sqlite3
import pandas as pd
from pandas import DataFrame
from abc import ABC, abstractmethod

# Class Handler (superclass)
class Handler:
    def __init__(self):
        self.dbPathOrUrl = ""
    
    def getDbPathOrUrl(self):
        return self.dbPathOrUrl
    
    #Qui per ora copiato dal Pres ma non ho capito troppo come funziona
    def setDbPathOrUrl(self, dbPathOrUrl: str) -> bool:
        try:
            self.dbPathOrUrl = dbPathOrUrl
            return True
        except Exception as e:
            return False
        

# Upload Handler

class UploadHandler(Handler):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def pushDataToDb(self, path: str) -> bool:
        pass
    
# Bibliographic Entity Upload Handler
class BibliographicEntityUploadHandler(UploadHandler):
    def __init__(self):
       super().__init__()


#Qui la parte che prende il JSON e lo trasforma in relational database!!!
    def pushDataToDb(self, path):
        return super().pushDataToDb(path)


class QueryHandler(Handler):
    def __init__(self):
        super().__init__()

    def getById(self, id: str):
        pass

# Qui il query handler, usando SQL
class BibliographicEntityQueryHandler(QueryHandler, Handler):
    def __init__(self):
        super().__init__()

    def getAllBibliographicEntities():
        pass

    def  getBibliographicEntitiesWithTitle():
        pass

    def  getBibliographicEntitiesWithAuthor():
        pass

    def getBibliographicEntitiesWithinPublicationDate():
        pass

    def getBibliographicEntitiesWithVenue():
        pass
