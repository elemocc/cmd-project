# Importo cose necessarie
import json
import sqlite3
import pandas as pd
from pandas import DataFrame
from abc import ABC, abstractmethod
import re

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


# Creo una funzione che converte una data parziale (YYYY, YYYY-MM, YYYY-MM-DD) 
# in un formato YYYY-MM-DD completo, usando 01 come mese/giorno 
# di default quando mancanti. Restituisce stringa vuota se il formato 
# non è valido o il valore è vuoto. Sarà necessaria per normalizzare i dati della publication date prima 
# di pusharli nel database e evitare problemi nelle queries
def normalize_pub_date(date_str):
    if not date_str:
        return ""
    
    date_str = date_str.strip()
    match = re.match(r"^(\d{4})(-(\d{2}))?(-(\d{2}))?$", date_str)
    if match is None:
        return ""
    
    year = match.group(1)
    month = match.group(3) or "01"
    day = match.group(5) or "01"
    return f"{year}-{month}-{day}"

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

            df["pub_date"] = df["pub_date"].apply(self.normalize_pub_date)
                
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

    def getBibliographicEntitiesWithinPublicationDate(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    
        def pad_start(date_str):
            """Completa una data parziale interpretandola come inizio periodo."""
            if not date_str:
                return None
            date_str = date_str.strip()
            if len(date_str) == 4:       # solo anno: "2022"
                return date_str + "-01-01"
            if len(date_str) == 7:       # anno-mese: "2022-10"
                return date_str + "-01"
            return date_str              # già completa: "2022-10-23"

        def pad_end(date_str):
            """Completa una data parziale interpretandola come fine periodo."""
            if not date_str:
                return None
            date_str = date_str.strip()
            if len(date_str) == 4:       # solo anno: "2022"
                return date_str + "-12-31"
            if len(date_str) == 7:       # anno-mese: "2022-10"
            # Nota: usare sempre "-31" non è corretto per mesi più corti
            # (es. novembre ha 30 giorni), ma per il confronto tra stringhe non crea problemi
                return date_str + "-31"
            return date_str

        start_date = pad_start(start_date)
        end_date = pad_end(end_date)

        with sqlite3.connect(self.getDbPathOrUrl()) as con:
            where_clauses = ["1=1"]
            params = []

            if start_date:
                where_clauses.append("BibliographicEntity_Metadata.pub_date >= ?")
                params.append(start_date)

            if end_date:
                where_clauses.append("BibliographicEntity_Metadata.pub_date <= ?")
                params.append(end_date)

            query = f"""
                SELECT BibliographicEntity_Metadata.internal_id, title, pub_date, venue,
                       GROUP_CONCAT(DISTINCT BibliographicEntity_Authors.author, ';') as authors,
                       GROUP_CONCAT(DISTINCT BibliographicEntity_ID.id, ';') as ids
                FROM BibliographicEntity_Metadata
                LEFT JOIN BibliographicEntity_Authors 
                    ON BibliographicEntity_Metadata.internal_id = BibliographicEntity_Authors.internal_id
                LEFT JOIN BibliographicEntity_ID 
                    ON BibliographicEntity_Metadata.internal_id = BibliographicEntity_ID.internal_id
                WHERE {" AND ".join(where_clauses)}
                GROUP BY BibliographicEntity_Metadata.internal_id
            """
            return pd.read_sql(query, con, params=params)
    

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
