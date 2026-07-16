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

# I dati contenuti nel JSON sono strutturati come in esempio:
# {
#   "title": "...",
#   "author": ["Nome1", "Nome2"],
#   "pub_date": "...",
#   "venue": "...",
#   "id": ["omid:br/...", "doi:...", "isbn:..."]
# }

class BibliographicEntityUploadHandler(UploadHandler):
    def __init__(self):
       super().__init__()

#I dati dal JSON vengono inseriti nel relational database

class BibliographicEntityUploadHandler(UploadHandler):
    def __init__(self):
       super().__init__()

    # I dati dal JSON vengono inseriti nel database relazionale
    def pushDataToDb(self, path):
        try: # Logica try/except così che eventuali file danneggiati vengano segnalati
            # Lettura del file JSON
            with open(path, "r", encoding="utf-8") as f:
                raw_data = json.load(f) # -> oggetto python: lista di dizionari
                
            df = pd.json_normalize(raw_data) #dataframe creato con normalizzazione delle strutture nested
            
            # Creo codice id interno univoco
            df["internal_id"] = ["internal_" + str(i) for i in range(len(df))]
            
            # Normalizzo tutti i valori vuoti convertendoli in stringhe vuote per i keys 
            # che hanno una sola stringa (titolo, publication date, venue)
            for col in ["title", "pub_date", "venue"]:
                df[col] = df[col].fillna("").astype(str).str.strip()
                
            # Li salvo in una tabella che contiene solo questi metadati
            bibliographic_entity = df[["internal_id", "title", "pub_date", "venue"]]
            
            # Gestione delle keys che possono contenere più valori: creo tabelle apposite per Autori e ID
            authors_table = df[["internal_id", "author"]].explode("author")
            authors_table["author"] = authors_table["author"].fillna("").astype(str).str.strip() # gestione delle keys vuote -> ""
            
            id_table = df[["internal_id", "id"]].explode("id")
            id_table["id"] = id_table["id"].fillna("").astype(str).str.strip()
            id_table = id_table[id_table["id"] != ""]
            
            # Carico le tre tabelle (dataframe) su SQLite
            db_path = self.getDbPathOrUrl()
            with sqlite3.connect(db_path) as conn:
                bibliographic_entity.to_sql(
                    "BibliographicEntity_Metadata", conn, if_exists="replace", index=False
                )
                authors_table.to_sql(
                    "BibliographicEntity_Authors", conn, if_exists="replace", index=False
                )
                id_table.to_sql(
                    "BibliographicEntity_ID", conn, if_exists="replace", index=False
                )
            return True
            
        except Exception as e:
            print(f"Error during upload: {e}")
            return False


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
