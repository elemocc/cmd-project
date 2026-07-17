from rdflib import Graph, URIRef, Literal, RDF, Namespace, XSD
from SPARQLWrapper import SPARQLWrapper, POST, DIGEST
from urllib.error import URLError
from SPARQLWrapper.SPARQLExceptions import SPARQLWrapperException
import re
import pandas as pd
from csv import DictReader


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
    def pushDataToDb(self, path: str) -> bool: 
        pass


# –––––––––––––––––––––– CitationUploadHandler  ––––––––––––––––––––––

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
                cited_entity = URIRef(self.base_url + "/res" + row["cited"].replace(":", "-"))

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

                # Adding the date: creating a Literal specifyng the type as XSD.date
                if row["creation"]:
                    my_graph.add((subj, creation, Literal(row["creation"], datatype=XSD.date)))

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

# –––––––––––––––––––––– CitationQueryHandler  ––––––––––––––––––––––

class CitationQueryHandler(QueryHandler):






    


 









