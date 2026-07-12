# Class Handler con attributi dbPathorUrl; metodi getDbpathorurl, set dbpathorurl
class Handler:
    def __init__(self):
        self.DbPathOrUrl = str
    
    def getDbPathOrUrl(self):
        return self.DbPathOrUrl
    
    #GIÀ QUI NON STO PIù CAPENDO COME FUNZIONA
    def setDbPathOrUrl(self):
        try:
            self.DbPathOrUrl = DbPathOrUrl
            return True
        except Exception as e:
            return False

# Class uploadhandler con metodi pushdatatodb

class UploadHandler(Handler):
    def __init__(self):
        super().__init__()

    #@abstractmethod
    #def PushDataToDb(self, path: str):
    
# Class bibliographichentityuploadhandler
#Class bibliographichentityqueryhandler