# Importo cose necessarie
import json
import sqlite3
import pandas as pd
from pandas import DataFrame

# Class Handler (superclass)
class Handler:
    def __init__(self):
        self.DbPathOrUrl = str
    
    def getDbPathOrUrl(self):
        return self.DbPathOrUrl
    
    #GIÀ QUI NON STO PIù CAPENDO COME FUNZIONA
    def setDbPathOrUrl(self, pathOrUrl: str) -> bool:
        try:
            self.dbPathOrUrl = pathOrUrl
            return True
        except Exception as e:
            return False
        

# Upload Handler

class UploadHandler(Handler):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def PushDataToDb(self, path: str) -> bool:
        pass
    
# Bibliographic Entity Upload Handler
class BibliographicEntityUploadHandler(UploadHandler, Handler):
    def __init__(self):
       super().__init__()

    def PushDataToDb(self, path):
        #return super().PushDataToDb(path)

#Query Handler
class QueryHandler(Handler):
    def __init__(self):
        super().__init__()

    def getById:
        pass

#Bibliographichentityqueryhandler
class BibliographicEntityQueryHandler(QueryHandler, Handler):
    def __init__(self):
        super().__init__()
