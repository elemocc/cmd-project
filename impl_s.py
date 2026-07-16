# Importo cose necessarie
import json
import sqlite3
import pandas as pd
from pandas import DataFrame
from abc import ABC, abstractmethod

# Per calcoalre il timespan, che servirà in una query successiva
def iso_duration_to_days(duration):
    """Converting a timespan from a string in ISO8601 duration format where 
    it's present in the total number of days using RegEx"""
    if not duration:
        return None
    m = re.match(r"P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)D)?", duration)
    if m is None:
        return None
    years, months, days = (int(x) if x else 0 for x in m.groups())
    return years * 365 + months * 30 + days


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
            
            # come internal identifier è stato scelto omid in quanto presente in tutte le istanze del dataset di prova
            # e per coerenza con quanto fatto nel graph database
            def extract_omid(id_list):
                for identifier in id_list:
                    if identifier.startswith("omid:"):
                        return identifier.replace(":", "-")
                return None 
            df["internal_id"] = df["id"].apply(extract_omid)
            
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


class QueryHandler(Handler, ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def getById(self, id: str) -> pd.DataFrame:
        pass

# Qui il query handler, usando SQL
class BibliographicEntityQueryHandler(QueryHandler):
    def __init__(self):
        super().__init__()
    
    def getById(self, id:str) -> pd.DataFrame:
        with sqlite3.connect(self.getDbPathOrUrl()) as con:
            query = """
                SELECT BibliographicEntity_Metadata.internal_id, title, pub_date, venue,
                       GROUP_CONCAT(DISTINCT BibliographicEntity_Authors.author) as authors,
                       GROUP_CONCAT(DISTINCT BibliographicEntity_ID.id) as ids
                FROM BibliographicEntity_Metadata
                LEFT JOIN BibliographicEntity_Authors 
                    ON BibliographicEntity_Metadata.internal_id = BibliographicEntity_Authors.internal_id
                LEFT JOIN BibliographicEntity_ID 
                    ON BibliographicEntity_Metadata.internal_id = BibliographicEntity_ID.internal_id
                WHERE BibliographicEntity_Metadata.internal_id IN (
                    SELECT internal_id FROM BibliographicEntity_ID WHERE id = ?
                )
                GROUP BY BibliographicEntity_Metadata.internal_id
            """   
        return pd.read_sql(query, con, params=(id,))

    def getAllBibliographicEntities(self):
        with sqlite3.connect(self.getDbPathOrUrl()) as con:
            query = """
                SELECT BibliographicEntity_Metadata.internal_id, title, pub_date, venue,
                       GROUP_CONCAT(DISTINCT BibliographicEntity_Authors.author) as authors,
                       GROUP_CONCAT(DISTINCT BibliographicEntity_ID.id) as ids
                FROM BibliographicEntity_Metadata
                LEFT JOIN BibliographicEntity_Authors 
                    ON BibliographicEntity_Metadata.internal_id = BibliographicEntity_Authors.internal_id
                LEFT JOIN BibliographicEntity_ID 
                    ON BibliographicEntity_Metadata.internal_id = BibliographicEntity_ID.internal_id
                GROUP BY BibliographicEntity_Metadata.internal_id
            """   
        return pd.read_sql(query, con)

    def  getBibliographicEntitiesWithTitle(self, title):
        with sqlite3.connect(self.getDbPathOrUrl()) as con:
            query = """
            SELECT BibliographicEntity_Metadata.internal_id, title, pub_date, venue,
                       GROUP_CONCAT(DISTINCT BibliographicEntity_Authors.author) as authors,
                       GROUP_CONCAT(DISTINCT BibliographicEntity_ID.id) as ids
                FROM BibliographicEntity_Metadata
                LEFT JOIN BibliographicEntity_Authors 
                    ON BibliographicEntity_Metadata.internal_id = BibliographicEntity_Authors.internal_id
                LEFT JOIN BibliographicEntity_ID 
                    ON BibliographicEntity_Metadata.internal_id = BibliographicEntity_ID.internal_id
                WHERE BibliographicEntity_Metadata.title LIKE ?
                GROUP BY BibliographicEntity_Metadata.internal_id    
            """   
        return pd.read_sql(query, con, params=(title,)) 
    
    # !!! QUI NON HO CAPITO BENE COME VADA FORMATTATO IL TITOLO PER LA QUERY

    def  getBibliographicEntitiesWithAuthor(self, author):
        with sqlite3.connect(self.getDbPathOrUrl()) as con:
            query = """
            SELECT BibliographicEntity_Metadata.internal_id, title, pub_date, venue,
                       GROUP_CONCAT(DISTINCT BibliographicEntity_Authors.author) as authors,
                       GROUP_CONCAT(DISTINCT BibliographicEntity_ID.id) as ids
                FROM BibliographicEntity_Metadata
                LEFT JOIN BibliographicEntity_Authors 
                    ON BibliographicEntity_Metadata.internal_id = BibliographicEntity_Authors.internal_id
                LEFT JOIN BibliographicEntity_ID 
                    ON BibliographicEntity_Metadata.internal_id = BibliographicEntity_ID.internal_id
                WHERE BibliographicEntity_Metadata.author LIKE ?
                GROUP BY BibliographicEntity_Metadata.internal_id    
            """   
        return pd.read_sql(query, con, params=(author,))

    def getBibliographicEntitiesWithinPublicationDate(self, start_date, end_date):
        with sqlite3.connect(self.getDbPathOrUrl()) as con:
            query = """
                
            """   
        return pd.read_sql(query, con, params=(start_date, end_date,))

    def getBibliographicEntitiesWithVenue(self, venue):
        with sqlite3.connect(self.getDbPathOrUrl()) as con:
            query = """
            SELECT BibliographicEntity_Metadata.internal_id, title, pub_date, venue,
                       GROUP_CONCAT(DISTINCT BibliographicEntity_Authors.author) as authors,
                       GROUP_CONCAT(DISTINCT BibliographicEntity_ID.id) as ids
                FROM BibliographicEntity_Metadata
                LEFT JOIN BibliographicEntity_Authors 
                    ON BibliographicEntity_Metadata.internal_id = BibliographicEntity_Authors.internal_id
                LEFT JOIN BibliographicEntity_ID 
                    ON BibliographicEntity_Metadata.internal_id = BibliographicEntity_ID.internal_id
                WHERE BibliographicEntity_Metadata.venue LIKE ?
                GROUP BY BibliographicEntity_Metadata.internal_id    
            """   
        return pd.read_sql(query, con, params=(venue,))
