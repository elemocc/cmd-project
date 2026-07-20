from rdflib import Graph, URIRef, Literal, RDF, Namespace, XSD
from SPARQLWrapper import SPARQLWrapper, POST, DIGEST, JSON
from urllib.error import URLError
from SPARQLWrapper.SPARQLExceptions import SPARQLWrapperException
import re
import pandas as pd
from csv import DictReader
from abc import ABC, abstractmethod    

# Class Handler (superclass)
class Handler:
    def __init__(self):
        self.dbPathOrUrl = ""
    
    def getDbPathOrUrl(self):
        return self.dbPathOrUrl
    
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

    def pushDataToDb(self, path: str) -> bool:
        raise NotImplementedError
    
class QueryHandler(Handler):
    def __init__(self):
        super().__init__()

    def getById(self, id: str) -> pd.DataFrame:
        raise NotImplementedError

# Alice Machieraldo ––––––––––– CitationUploadHandler –––––––––––

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

def normalize_creation_date(date_str):
    """Porta le date parziali (YYYY o YYYY-MM) al formato completo YYYY-MM-DD
    richiesto da xsd:date"""
    if not date_str:
        return None
    date_str = date_str.strip()
    if len(date_str) == 4:        # "2010" -> "2010-01-01"
        return date_str + "-01-01"
    if len(date_str) == 7:        # "2010-03" -> "2010-03-01"
        return date_str + "-01"
    return date_str               # già completa (YYYY-MM-DD)

class CitationUploadHandler(UploadHandler): 
    """This class implements the method of the superclass to handle 
    specific scenario, i.e., to handle CSV files in input and store 
    their data in a graph database"""  
    def __init__(self):
        super().__init__()
    
    # The function for reading the CSV file and creating the graph
    def pushDataToDb(self, path: str) -> bool:
        """The string defining the base URL used to define the URLs
        of all the resources created from the data"""
        self.base_url = "https://example.org/"
        my_graph = Graph()

        # Classes Resources
        Citation = URIRef(self.base_url + "vocab/Citation")
        Author_SC = URIRef(self.base_url + "vocab/AuthorSelfCitation")
        Journal_SC = URIRef(self.base_url + "vocab/JournalSelfCitation")

        # attributes of the resources
        creation = URIRef(self.base_url + "vocab/hasCreationDate")
        duration_prop = URIRef(self.base_url + "vocab/hasDuration")
        duration_days_prop = URIRef(self.base_url + "vocab/hasDurationDays")

        # relations between resources
        citing_prop = URIRef(self.base_url + "vocab/hasCitingEntity")
        cited_prop = URIRef(self.base_url + "vocab/hasCitedEntity")

        # Opening the csv file and close it automatically at the end of the indented block
        with open(path, "r", encoding="utf-8") as f: 
            reader_csv = DictReader(f) # Reading the csv with the first row as the header
            for row in reader_csv: # A for loop through the csv in order to construct the nodes of the graph
                subj = URIRef(self.base_url + "res/citation-" + row["oci"]) # The creation of the URI for citation 
                """ The creation of the URI for citing entity and for the cited entity, also
                replacing ":" with "-" for a matter of URI syntax
                """
                citing_entity = URIRef(self.base_url + "res/" + row["citing"].replace(":", "-")) 
                cited_entity = URIRef(self.base_url + "res/" + row["cited"].replace(":", "-"))

                """ Adding to the graph the triple (subject, predicate, object) 
                using the syntax for tuples, taking as subject the specific URI, 
                the RDF.type as predicate to specify the data type, 
                and the specific class Citation as the object """
                my_graph.add((subj, RDF.type, Citation)) 

                """ If a subject has more than one type: the subject remain the same
                but the object can be more than one. In these two following cases, the same
                subject and the same precidate have three different objects, three different 
                triples that can coexist within the same subject in RDF. 
                This will be usefull managing the queries """
                if row["author_sc"].strip().lower() == "yes":
                    my_graph.add((subj, RDF.type, Author_SC))
                if row["journal_sc"].strip().lower() == "yes":
                    my_graph.add((subj, RDF.type, Journal_SC))

                # Adding to the graph the relations between entities
                my_graph.add((subj, citing_prop, citing_entity))
                my_graph.add((subj, cited_prop, cited_entity))

                # Adding the date: normalizing partial dates (YYYY / YYYY-MM) before
                # creating a Literal typed as XSD.date, otherwise rdflib fails on serialization
                if row["creation"]:
                    norm_creation = normalize_creation_date(row["creation"])
                    if norm_creation:
                        try:
                            my_graph.add((subj, creation, Literal(norm_creation, datatype=XSD.date)))
                        except Exception as e:
                            print(f"Skipping invalid creation date '{row['creation']}' for {row['oci']}: {e}")

                """ Adding the timespan: saving the original value as a string
                then calling the function iso_duration_days for retrieving the
                amount of days, then adding a second triple specified as XSD.integer """
                if row["timespan"]:
                    my_graph.add((subj, duration_prop, Literal(row["timespan"])))
                    days = iso_duration_to_days(row["timespan"])
                    if days is not None:
                        my_graph.add((subj, duration_days_prop, Literal(days, datatype=XSD.integer)))

        """ At the end of the for loop the file will be closed and the graph will 
         contain all triples from all the citations """
        return self._upload_graph(my_graph)
    
    # The function for pushing the graph to Blazegraph that takes as inputs: self, the graph and the batch size
    def _upload_graph(self, g, batch_size=200):
        """ Uploading triples on Blazegraph by batches, to avoid query too big """
        try: 
            triples = list(g) # Transforming the graph into a list of tuples (subject, predicate, object)
            for i in range(0, len(triples), batch_size): # Number of iteration depends on the number of triples and the batch size
                batch = triples[i:i + batch_size] # Slicing over the list of triples depending on the batch size
                """ Setting the string for SPARQL query assigning for every triple the three variables 
                # s (subject), p (predicate), o (object) to a string in SPARQL syntax using
                # rdflib n.3() method to convert an URI or a Literal. Then joining all the strings together """
                insert_data = " .\n".join(
                    f"{s.n3()} {p.n3()} {o.n3()}" for s, p, o in batch
                ) 
                """ To insert the value of the variable insert_data 
                (the string with all the triple) into the query text
                Also adding the last "." terminating the last triple for SPARQL syntax """
                query = f"INSERT DATA {{ {insert_data} . }}" 

                """ This following block will be repeated for every batch """
                sparql = SPARQLWrapper(self.dbPathOrUrl) # Creating an object to communicate with SPARQL endpoint
                sparql.setMethod(POST) # The method POST is necessary with INSERT DATA
                sparql.setQuery(query) # Setting the query text from the query above
                sparql.query() # Executing the query via Blazegraph sending triples

            return True # True stands for successfull upload

        # In case of fail
        except (URLError, SPARQLWrapperException) as e: 
            print(f"Communication error with Blazegraph: {e}")
            return False    


# Alice Machieraldo ––––––––––– CitationQueryHandler –––––––––––

class CitationQueryHandler(QueryHandler):
    def __init__(self):
        super().__init__()


    def _run_query(self, query):
        sparql = SPARQLWrapper(self.dbPathOrUrl) # Creating a SPARQLWrapper object pointed to the SPARQL endpoint (Blazegraph URL)
        sparql.setQuery(query) # Setting the text for SPARQL query
        sparql.setReturnFormat(JSON) # Asking Blazegraph endpoint to reply in JSON format

        #.query() will execute the query via Blazegraph, 
        # then .convert() will transform it ina Python dictionary because we set JSON format above
        results = sparql.query().convert()
        

        assert isinstance(results, dict) 
        """ This line does two things at once:
        At RUNTIME: it actually checks that "results" really is a dict.
        If it's not, the program stops here with a clear AssertionError,
        instead of failing later with a more confusing error.
        For Pylance: "type narrowing", from this line onward, Pylance 
        "trusts" that results is a dict.
        """

        rows = []
        for binding in results["results"]["bindings"]: 
            # Iterating over the list of rows found by the query: 
            # "binding" is one single row of the SPARQL result
            #e.g. {"citation": {"type": "uri", "value": "..."}, "citing": {...}}
            rows.append({k: v["value"] for k, v in binding.items()}) 
            # we keep only the actual value of each variable, discarding "type"/"datatype"
        
        """Converting the list of dictionaries in a pandas frame: 
        every dictionary is a row and every key is the name of a column"""
        return pd.DataFrame(rows) 
    
    # Implementing getById for the QueryHandler
    def getById(self, id: str) -> pd.DataFrame:
        # Costruisco direttamente l'URI del soggetto, invece di usare
        base_url = getattr(self, "base_url", "https://example.org/")
        citation_uri = f"<{base_url}res/citation-{id}>"

        query = f"""
        PREFIX vocab: <https://example.org/vocab/>

        SELECT ?citation ?citing ?cited ?creation ?duration ?days
        WHERE {{
            BIND({citation_uri} AS ?citation)
            ?citation a vocab:Citation ;
                      vocab:hasCitingEntity ?citing ;
                      vocab:hasCitedEntity ?cited .

            OPTIONAL {{ ?citation vocab:hasCreationDate ?creation }}
            OPTIONAL {{ ?citation vocab:hasDuration ?duration }}
            OPTIONAL {{ ?citation vocab:hasDurationDays ?days }}
        }}
        """

        df = self._run_query(query)

        if not df.empty:
            if "creation" in df.columns:
                df["creation"] = pd.to_datetime(df["creation"], errors="coerce")
            if "days" in df.columns:
                df["days"] = pd.to_numeric(df["days"], errors="coerce")

        return df
   
    def getAllCitations(self):
        """Return all citations including the ones without a known creation
        date or duration (which is OPTIONAL)"""
        query = """
        PREFIX vocab: <https://example.org/vocab/>
        SELECT ?citation ?citing ?cited ?creation ?duration WHERE {
            ?citation a vocab:Citation ;
                      vocab:hasCitingEntity ?citing ;
                      vocab:hasCitedEntity ?cited .
            OPTIONAL { ?citation vocab:hasCreationDate ?creation }
            OPTIONAL { ?citation vocab:hasDuration ?duration }
        }
        """
        df = self._run_query(query)

        # Conveting the values from SPARQL from strings to real datetime for the
        # date column when present (checking if there is a column for "creation" as it
        # is optional)
        if not df.empty and "creation" in df.columns:
            df["creation"] =pd.to_datetime(df["creation"], errors="coerce")
            # errors="coerce": invalid/missing dates become NaT instead of raising error

        return df

    def getAllAuthorSelfCitations(self):
        """Return only the citations flagged as author self-citations 
        (author_sc == "yes" in the original CSV)"""
        query = """
        PREFIX vocab: <https://example.org/vocab/>
        SELECT ?citation ?citing ?cited WHERE {
            ?citation a vocab:AuthorSelfCitation ;
                      vocab:hasCitingEntity ?citing ; 
                      vocab:hasCitedEntity ?cited .
        }
        """
        return self._run_query(query)
    
    def getAllJournalSelfCitations(self):
        """Return only the citations flagged as journal self-citations
        (journal_sc == "yes" in the original CSV)"""
        query = """
        PREFIX vocab: <https://example.org/vocab/>
        SELECT ?citation ?citing ?cited WHERE {
            ?citation a vocab:JournalSelfCitation ;
                      vocab:hasCitingEntity ?citing ;
                      vocab:hasCitedEntity ?cited .
        }
        """
        return self._run_query(query)
    
    def getCitationsWithinDate(self, min_date=None, max_date=None):
        """Return citations whose creation date falls within [min_date, max_date].
        Both bounds are optional: if one is missing, that side is unbounded"""

        def pad_start(date_str):
            if not date_str:
                return None
            date_str = date_str.strip()
            if len(date_str) == 4:      # YYYY
                return date_str + "-01-01"
            if len(date_str) == 7:      # YYYY-MM
                return date_str + "-01"
            return date_str

        def pad_end(date_str):
            if not date_str:
                return None
            date_str = date_str.strip()
            if len(date_str) == 4:      # YYYY
                return date_str + "-12-31"
            if len(date_str) == 7:      # YYYY-MM
                return date_str + "-31"
            return date_str

        min_date = pad_start(min_date)
        max_date = pad_end(max_date)
            
        # Build the FILTER clauses dynamically, only for the bounds provided
        filters = []
        if min_date:
            filters.append(f'FILTER (?creation >= "{min_date}"^^xsd:date)')
        if max_date:
            filters.append(f'FILTER (?creation <= "{max_date}"^^xsd:date)')

        # here "creation" can't be optional so the check will always be True
        query = f"""
        PREFIX vocab: <https://example.org/vocab/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        SELECT ?citation ?citing ?cited ?creation WHERE {{
            ?citation a vocab:Citation ;
                      vocab:hasCitingEntity ?citing ;
                      vocab:hasCitedEntity ?cited ;
                      vocab:hasCreationDate ?creation .
            {' '.join(filters)}
        }} 
        """
        df = self._run_query(query)

        if not df.empty and "creation" in df.columns:
            df["creation"] = pd.to_datetime(df["creation"], errors="coerce")
        # if a value is not convertible, pandas will substitute it with NaT ("Not a Time")

        return df
    
    def getCitationsWithinTimespan(self, min_span=None, max_span=None):
        """ Return citations whose duration (timespan) falls within
        [min_span, max_span] both given as ISO8601 duration strings. 
        The comparison happens on the precomputed "days" value not on
        the ISO string itself"""
        
        # Convert the input bounds (ISO duration strings) into days too 
        # to compare numbers against numbers
        min_days = iso_duration_to_days(min_span) if min_span else None
        max_days = iso_duration_to_days(max_span) if max_span else None

        filters = []
        if min_days is not None:
            filters.append(f"FILTER (?days >= {min_days})")
        if max_days is not None:
            filters.append(f"FILTER (?days <= {max_days})")

        query = f"""
        PREFIX vocab: <https://example.org/vocab/>
        SELECT ?citation ?citing ?cited ?duration ?days WHERE {{
            ?citation a vocab:Citation ;
                      vocab:hasCitingEntity ?citing ;
                      vocab:hasCitedEntity ?cited ;
                      vocab:hasDuration ?duration ;
                      vocab:hasDurationDays ?days .
            {' '.join(filters)}
        }}
        """
        df = self._run_query(query)

        # "days" comes back as text so convert it to a number 
        if not df.empty and "days" in df.columns:
            df["days"] = pd.to_numeric(df["days"])

        return df










    


 









