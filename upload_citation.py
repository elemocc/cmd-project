from rdflib import Graph, URIRef, Literal, RDF, Namespace, XSD
from pandas import read_csv, Series
from SPARQLWrapper import SPARQLWrapper, POST, DIGEST
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
    def pushDataToDb(self, path: str): 
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

        with open(path, "r", encoding="utf-8") as f: # Opening the csv file and close it automatically at the end of the indented block
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


                my_graph.add((subj, citing_prop, citing_entity))
                my_graph.add((subj, cited_prop, cited_entity))
                



    


 









