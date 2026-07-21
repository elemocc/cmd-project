# Silvia Baldassarri ––––––––––– BibliographicEntityUploadHandler –––––––––––

def normalize_pub_date(date_str):
    """Converting a partial publication date (YYYY, YYYY-MM or YYYY-MM-DD) into
    a complete YYYY-MM-DD format, using "01" as the default month/day when
    missing"""
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

class BibliographicEntityUploadHandler(UploadHandler):
    """This class implements the method of the superclass to handle the
    bibliographic metadata scenario, i.e., to handle JSON files in input
    and store their data in a relational database"""
    def __init__(self):
       super().__init__()

    # The function for reading the JSON file and populating the relational database
    def pushDataToDb(self, path):
        try: # try/except block so that any corrupted or unreadable file gets reported instead of crashing the whole upload
            # Opening the JSON file and closing it automatically at the end of the indented block
            with open(path, "r", encoding="utf-8") as f:
                raw_data = json.load(f) # -> Python object: a list of dictionaries
                
            df = pd.json_normalize(raw_data) # Creating the DataFrame, flattening any nested structure
            
            
            """ omid was chosen as the internal identifier because it is present
            in every instance of the test dataset, and for consistency with what
            is done in the graph database. If present, instances without an omid
            are discarded; this is reported by comparing the number of instances
            before and after the filtering, printing a message to the terminal """

            def extract_omid(id_list):
                if not isinstance(id_list, list):
                    return None
                for identifier in id_list:
                    if identifier.startswith("omid:"):
                        return identifier.replace(":", "-")
                return None

            before = len(df) # Number of instances before discarding the ones without omid
            df["internal_id"] = df["id"].apply(extract_omid)
            df = df.dropna(subset=["internal_id"])
            after = len(df) # Number of instances after discarding the ones without omid
            if before != after:
                print(f"Attenzione: {before - after} record scartati per omid mancante")
            
            # Normalizing all the empty values into empty strings for the keys
            # that hold a single string (title, publication date, venue)
            for col in ["title", "pub_date", "venue"]:
                df[col] = df[col].fillna("").astype(str).str.strip()

            df["pub_date"] = df["pub_date"].apply(normalize_pub_date)
                
            # Saving these columns into a dedicated table containing only the metadata
            bibliographic_entity = df[["internal_id", "title", "pub_date", "venue"]]
            
            """ Handling the keys that can hold more than one value: creating
            dedicated tables for Authors and ID, exploding the lists so that
            every element gets its own row with the same internal_id """
            authors_table = df[["internal_id", "author"]].explode("author")
            authors_table["author"] = authors_table["author"].fillna("").astype(str).str.strip() # gestione delle keys vuote -> ""
            
            id_table = df[["internal_id", "id"]].explode("id")
            id_table["id"] = id_table["id"].fillna("").astype(str).str.strip()
            id_table = id_table[id_table["id"] != ""]
            
            # Loading the three tables (DataFrames) into SQLite
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

        # In case of fail    
        except Exception as e:
            print(f"Error during upload: {e}")
            return False

# Silvia Baldassarri ––––––––––– BibliographicEntityUploadHandler –––––––––––

class BibliographicEntityQueryHandler(QueryHandler):
    """This class implements the method of the superclass to query the
    bibliographic metadata stored in the relational database, using SQL"""
    def __init__(self):
        super().__init__()
    
    def getById(self, id:str) -> pd.DataFrame:
        with closing(sqlite3.connect(self.getDbPathOrUrl())) as con:
            query = """
                SELECT BibliographicEntity_Metadata.internal_id, title, pub_date, venue,
                       GROUP_CONCAT(BibliographicEntity_Authors.author, ';') as authors,
                       GROUP_CONCAT(BibliographicEntity_ID.id, ';') as ids
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
        with closing(sqlite3.connect(self.getDbPathOrUrl())) as con:
            query = """
                SELECT BibliographicEntity_Metadata.internal_id, title, pub_date, venue,
                       GROUP_CONCAT(BibliographicEntity_Authors.author, ';') as authors,
                       GROUP_CONCAT(BibliographicEntity_ID.id, ';') as ids
                FROM BibliographicEntity_Metadata
                LEFT JOIN BibliographicEntity_Authors 
                    ON BibliographicEntity_Metadata.internal_id = BibliographicEntity_Authors.internal_id
                LEFT JOIN BibliographicEntity_ID 
                    ON BibliographicEntity_Metadata.internal_id = BibliographicEntity_ID.internal_id
                GROUP BY BibliographicEntity_Metadata.internal_id
            """   
            return pd.read_sql(query, con)

    def  getBibliographicEntitiesWithTitle(self, title):
        with closing(sqlite3.connect(self.getDbPathOrUrl())) as con:
            query = """
            SELECT BibliographicEntity_Metadata.internal_id, title, pub_date, venue,
                       GROUP_CONCAT(BibliographicEntity_Authors.author, ';') as authors,
                       GROUP_CONCAT(BibliographicEntity_ID.id, ';') as ids
                FROM BibliographicEntity_Metadata
                LEFT JOIN BibliographicEntity_Authors 
                    ON BibliographicEntity_Metadata.internal_id = BibliographicEntity_Authors.internal_id
                LEFT JOIN BibliographicEntity_ID 
                    ON BibliographicEntity_Metadata.internal_id = BibliographicEntity_ID.internal_id
                WHERE BibliographicEntity_Metadata.title LIKE ?
                GROUP BY BibliographicEntity_Metadata.internal_id    
            """   
            return pd.read_sql(query, con, params=(f"%{title}%",)) 

    def  getBibliographicEntitiesWithAuthor(self, author):
        """Using a subquery on BibliographicEntity_Authors to first find the
        internal_id(s) matching the given author, so that the outer query can
        then aggregate all the co-authors for those entities: filtering
        directly on the aggregated "authors" column would otherwise lose all
        the co-authors of the matched entity"""
        with closing(sqlite3.connect(self.getDbPathOrUrl())) as con:
            query = """
            SELECT BibliographicEntity_Metadata.internal_id, title, pub_date, venue,
                       GROUP_CONCAT(BibliographicEntity_Authors.author, ';') as authors,
                       GROUP_CONCAT(BibliographicEntity_ID.id, ';') as ids
                FROM BibliographicEntity_Metadata
                LEFT JOIN BibliographicEntity_Authors 
                    ON BibliographicEntity_Metadata.internal_id = BibliographicEntity_Authors.internal_id
                LEFT JOIN BibliographicEntity_ID 
                    ON BibliographicEntity_Metadata.internal_id = BibliographicEntity_ID.internal_id
                WHERE BibliographicEntity_Metadata.internal_id IN (
                SELECT internal_id FROM BibliographicEntity_Authors WHERE author LIKE ?
                )
                GROUP BY BibliographicEntity_Metadata.internal_id    
            """   
            return pd.read_sql(query, con, params=(f"%{author}%",))
        
        #qui ho fatto una "sottoquery" perché altrimenti si perdevano tutti i co-autori 

    def getBibliographicEntitiesWithinPublicationDate(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    
        def pad_start(date_str):
            """Completing a partial date, interpreting it as the start of the period"""
            if not date_str:
                return None
            date_str = date_str.strip()
            if len(date_str) == 4:       # year only: "2022"
                return date_str + "-01-01"
            if len(date_str) == 7:       # year-month: "2022-10"
                return date_str + "-01"
            return date_str              # already complete: "2022-10-23"

        def pad_end(date_str):
            """Completa una data parziale interpretandola come fine periodo."""
            if not date_str:
                return None
            date_str = date_str.strip()
            if len(date_str) == 4:       # year only: "2022"
                return date_str + "-12-31"
            if len(date_str) == 7:       # year-month: "2022-10"
            # Note: always using "-31" isn't strictly correct for shorter months
            # (e.g. November has 30 days), but it doesn't cause issues for string comparison
                return date_str + "-31"
            return date_str

        start_date = pad_start(start_date)
        end_date = pad_end(end_date)

        with closing(sqlite3.connect(self.getDbPathOrUrl())) as con:
            # Building the WHERE clauses dynamically, only for the bounds provided
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
                       GROUP_CONCAT(BibliographicEntity_Authors.author, ';') as authors,
                       GROUP_CONCAT(BibliographicEntity_ID.id, ';') as ids
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
        with closing(sqlite3.connect(self.getDbPathOrUrl())) as con:
            query = """
            SELECT BibliographicEntity_Metadata.internal_id, title, pub_date, venue,
                       GROUP_CONCAT(BibliographicEntity_Authors.author, ';') as authors,
                       GROUP_CONCAT(BibliographicEntity_ID.id, ';') as ids
                FROM BibliographicEntity_Metadata
                LEFT JOIN BibliographicEntity_Authors 
                    ON BibliographicEntity_Metadata.internal_id = BibliographicEntity_Authors.internal_id
                LEFT JOIN BibliographicEntity_ID 
                    ON BibliographicEntity_Metadata.internal_id = BibliographicEntity_ID.internal_id
                WHERE BibliographicEntity_Metadata.venue LIKE ?
                GROUP BY BibliographicEntity_Metadata.internal_id    
            """   
            return pd.read_sql(query, con, params=(f"%{venue}%",))

if __name__ == "__main__":
    handler= CitationQueryHandler()
    handler.setDbPathOrUrl("http://192.168.1.73:9999/blazegraph/sparql")

