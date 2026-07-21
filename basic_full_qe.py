import pandas as pd
from classes import *
from handlers import *

class BasicQueryEngine:
    def __init__(self): #create two empty lists when called
        self.citationQuery = []
        self.bibliographicEntityQuery = []
    
    def cleanCitationHandlers(self): #clean the handlers list by emptying the list
        self.citationQuery = []
        return True

    def cleanBibliographicEntityHandlers(self): #clean the handlers list by emptying the list
        self.bibliographicEntityQuery = []
        return True

    def addCitationHandler(self, handler: CitationQueryHandler) -> bool: #add the handler to the empty list created within the init   
        self.citationQuery.append(handler)
        return True 

    def addBibliographicEntityHandler(self, handler: BibliographicEntityQueryHandler) -> bool: #add the handler to the empty list creatd within the init
        self.bibliographicEntityQuery.append(handler)
        return True
    
    def getEntityById(self, id: str):   #search for a specified ID among the citations and/or the bibliographic entities contained in the two databases
        matchingIdEnt = pd.DataFrame()  #create an empty dataframe which will contain the possible matching bibliogrphic entity/citation returned by the handlers
        df_list = []    #create an empty list where to store the dataframes returned by the handlers
        for handler in self.bibliographicEntityQuery:   #ask each bibliographic entity query handler to retrieve a bibliographic entity (if any) having a matching id, and add it to a dataframe
            newDataFrame = handler.getById(id)  
            df_list.append(newDataFrame)    #the dataframe returned by the bibliographic entities query handler is appended to the df_list

        if  df_list:    # if the list is not empty (that is, it contains at least one dataframe), all the dataframes will be concatenated in a single df
            matchingIdEnt = pd.concat(df_list, ignore_index=True)

        if not matchingIdEnt.empty:     #check whether the dataframe is NOT empty, and only in that case proceed
            row = matchingIdEnt.iloc[0]     # consider only the first row in the dataframe (since only one row is expected) 
            
            bibEntWithId = BibliographicEntity()    #create a new python object having BibliographicEntity() class and extracting the attributes values from the dataframe row
            bibEntWithId.title = row["title"]
            bibEntWithId.authors = [row["authors"]]
            bibEntWithId.pub_date = row["pub_date"]
            bibEntWithId.venue = row["venue"]
            bibEntWithId.ids = [row["ids"]]

            return bibEntWithId
        
        else:                                   # if the first dataframe obtained by calling the BibliographicEntityQuery was empty (no bibliographic entity was found having such id), check if a matching id is contained within the citations
            matchingIdCit = pd.DataFrame()      #create an empty dataframe which will contain the possible matching bibliographic entity/citation returned by the handlers
            df_list = []                        
            for handler in self.citationQuery:  #ask each citation query handler to retrieve a citation (if any) having a matching id, and add it to a dataframe
                newDataFrame = handler.getById(id)
                df_list.append(newDataFrame)
            
            matchingIdCit = pd.concat(df_list, ignore_index=True)
            
            if not matchingIdCit.empty:             #check whether the dataframe is NOT empty, and only in that case proceed
                row = matchingIdCit.iloc[0]
                if row["journal_sc"] == "yes":      #create first a python object having the class AuthorSelfCitation or JournalSelfCitation, if needed, else create an object having the more generic class Citation
                    citWithId = JournalSelfCitation()
                
                elif row["author_sc"] == "yes":
                    citWithId = AuthorSelfCitation()
                
                else:
                    citWithId = Citation()
                
                citWithId.creation = row["creation"]        #extract the attributes values from the dataframe row
                citWithId.timespan = row["duration"]
                citWithId.ids = [row["citation"]]
                citWithId.hasCitingEntity = self.getEntityById(row["citing"])
                citWithId.hasCitedEntity = self.getEntityById(row["cited"])
                                    
                
                return citWithId

        return None



    
    def getAllCitations(self) -> list[Citation]:  #get all the citations from the handlers stored in the self.citationQuery list
        allCitations = pd.DataFrame()   #create a new empy dataframe where to store all the dataframes concatenated  
        df_list = []    #create an empty list which will contain all the dataframes from the handlers 
        for handler in self.citationQuery:  #ask each citation query handler to retrieve all the citations
            newDataFrame = handler.getAllCitations()   
            df_list.append(newDataFrame)        #append each dataframe to the initially empty df_list
        
        if not df_list: #if there were no dataframes and the df_list is therefore empty, the functions returns an empty list and won't try to concatenate an empty list of dataframe  
            return []
            

        allCitations = pd.concat(df_list, ignore_index=True)        #all the dataframes contained within the list will be concatenated in a single  dataframe
        
        all_citations = []
        for idx, row in allCitations.iterrows():        #for each dataframe row, create a corresponding Citation object having the same attributes values contained in the row
            citation = Citation()               
            citation.creation = row["creation"]
            citation.timespan = row["duration"]
            citation.ids = [row["citation"]]
            citation.hasCitingEntity = self.getEntityById(row["citing"])    # Convert the raw "citing" ID string into a fully instantiated BibliographicEntity object 
            citation.hasCitedEntity = self.getEntityById(row["cited"])      # Convert the raw "cited" ID string into a fully instantiated BibliographicEntity object 

            all_citations.append(citation)          #the new citation object is appended to the all_citations list
        
        return all_citations 
            
    def getAllBibliographicEntities(self):  #get all the bibliographic entities from the handlers stored in the self.bibliographicEntityQuery list
        allBibEnt = pd.DataFrame()  #create a new empy dataframe where to store all the dataframes concatenated 
        df_list = []                #create an empty list which will contain all the dataframes from the handlers
        for handler in self.bibliographicEntityQuery:   #ask each bibliographic entity query handler to retrieve all the bibliographic entities
            newDataFrame = handler.getAllBibliographicEntities()   
            df_list.append(newDataFrame)        #append each dataframe to the initially empty df_list
                            
        if not df_list: #if there were no dataframes and the df_list is therefore empty, the functions returns an empty list and won't try to concatenate an empty list of dataframe  
            return []
        
        allBibEnt = pd.concat(df_list, ignore_index=True)        #all the dataframe contained within the list will be concatenated in a single  dataframe


        all_bib_ent = []
        for idx, row in allBibEnt.iterrows():       #for each dataframe row, create a corresponding BibliographicEntity object having the same attributes values contained in the row
            bibEnt = BibliographicEntity() 
            bibEnt.title = row["title"]
            bibEnt.authors = [row["authors"]]
            bibEnt.pub_date = row["pub_date"]
            bibEnt.venue = row["venue"]
            bibEnt.ids = [row["ids"]] 

            all_bib_ent.append(bibEnt)      #the new bibliographic entity object is appended to the all_bib_ent list
        
        return all_bib_ent 
    

    def getBibliographicEntitiesWithTitle(self, title):
        df_list = [] 
        for handler in self.bibliographicEntityQuery:
            newDataFrame = handler.getBibliographicEntitiesWithTitle(title)   #NewDataFrame contains all the bib ent matching with the specified title
            df_list.append(newDataFrame)        #append each dataframe to the initially empty df_list
                            
        if not df_list: #if there were no dataframes and the df_list is therefore empty, the functions returns an empty list and won't try to concatenate an empty list of dataframe  
            return []
        
        bibEntWithTitle = pd.concat(df_list, ignore_index=True)     #create the dataframe bibEntWithTitle by concatenating all the dataframes contained in df_list

        all_bib_ent_title = []
        for idx, row in bibEntWithTitle.iterrows():     #for each dataframe row, create a corresponding BibliographicEntity object having the same attributes values contained in the row
            bibEnt = BibliographicEntity() 
            bibEnt.title = row["title"]
            bibEnt.authors = [row["authors"]]
            bibEnt.pub_date = row["pub_date"]
            bibEnt.venue = row["venue"]
            bibEnt.ids = [row["ids"]] 

            all_bib_ent_title.append(bibEnt)    #the new bibliographic entity object is appended to the all_bib_ent_title list
        
        return all_bib_ent_title           
    
    
    def getBibliographicEntitiesWithAuthor(self, author):
        df_list = [] 
        for handler in self.bibliographicEntityQuery:
            newDataFrame = handler.getBibliographicEntitiesWithAuthor(author)   #NewDataFrame contains all the bib ent matching with the specified author
            df_list.append(newDataFrame)        #append each dataframe to the initially empty df_list
                            
        if not df_list: #if there were no dataframes and the df_list is therefore empty, the functions returns an empty list and won't try to concatenate an empty list of dataframe  
            return []
        
        bibEntWithAuthor = pd.concat(df_list, ignore_index=True)     #create the dataframe bibEntWithAuthor by concatenating all the dataframes contained in df_list

        all_bib_ent_title = []
        for idx, row in bibEntWithAuthor.iterrows(): #for each dataframe row, create a corresponding BibliographicEntity object having the same attributes values contained in the row
            bibEnt = BibliographicEntity() 
            bibEnt.title = row["title"]
            bibEnt.authors = [row["authors"]]
            bibEnt.pub_date = row["pub_date"]
            bibEnt.venue = row["venue"]
            bibEnt.ids = [row["ids"]] 

            all_bib_ent_title.append(bibEnt)        #the new bibliographic entity object is appended to the all_bib_ent_author list
        
        return all_bib_ent_title
    
    def getBibliographicEntitiesWithVenue(self, venue: str) -> list[BibliographicEntity]:
        df_list = [] 
        for handler in self.bibliographicEntityQuery:
            newDataFrame = handler.getBibliographicEntitiesWithVenue(venue)   #NewDataFrame contains all the bib ent matching with the specified venue
            df_list.append(newDataFrame)        #append each dataframe to the initially empty df_list
                            
        if not df_list: #if there were no dataframes and the df_list is therefore empty, the functions returns an empty list and won't try to concatenate an empty list of dataframe  
            return []
        
        bibEntWithVenue = pd.concat(df_list, ignore_index=True)     #create the dataframe bibEntWithVenue by concatenating all the dataframes contained in df_list

        all_bib_ent_venue = []
        for idx, row in bibEntWithVenue.iterrows():     #for each dataframe row, create a corresponding BibliographicEntity object having the same attributes values contained in the row
            bibEnt = BibliographicEntity() 
            bibEnt.title = row["title"]
            bibEnt.authors = [row["authors"]]
            bibEnt.pub_date = row["pub_date"]
            bibEnt.venue = row["venue"]
            bibEnt.ids = [row["ids"]] 

            all_bib_ent_venue.append(bibEnt)    #the new bibliographic entity object is appended to the all_bib_ent_venue list
        
        return all_bib_ent_venue
    
    def getAllAuthorSelfCitations(self) -> list[AuthorSelfCitation]:
        df_list = []
        for handler in self.citationQuery:
            newDataFrame = handler.getAllAuthorSelfCitations()      #NewDataFrame contains all the citations which are also author self citations
            df_list.append(newDataFrame)
        
        if not df_list: #if there were no dataframes and the df_list is therefore empty, the functions returns an empty list and won't try to concatenate an empty list of dataframe  
            return []
        
        authorSelfCitDf = pd.concat(df_list, ignore_index=True)     #create the dataframe authorSelfCitDf by concatenating all the dataframes contained in df_list


        all_author_sc = []
        for idx, row in authorSelfCitDf.iterrows(): #for each dataframe row, create a corresponding AuthorSelfCitation object having the same attributes
            author_sc = AuthorSelfCitation()        
            author_sc.creation = row["creation"]
            author_sc.timespan = row["duration"]
            author_sc.hasCitingEntity = self.getEntityById(row["citing"]) # convert the raw "citing" ID string into a fully instantiated BibliographicEntity object 
            author_sc.hasCitedEntity = self.getEntityById(row["cited"])     # convert the raw "cited" ID string into a fully instantiated BibliographicEntity object
            author_sc.ids = [row["citation"]]

            all_author_sc.append(author_sc)     #the new AuthorSelfCitation object is appended to the all_author_sc list
        
        return all_author_sc
    
    def getAllJournalSelfCitations(self)-> list[JournalSelfCitation]:
        df_list = []
        for handler in self.citationQuery:
            newDataFrame = handler.getAllJournalSelfCitations()     #NewDataFrame contains all the citations which are also journal self citations
            df_list.append(newDataFrame)
        
        if not df_list: #if there were no dataframes and the df_list is therefore empty, the functions returns an empty list and won't try to concatenate an empty list of dataframe  
            return []
        
        journalSelfCitDf = pd.concat(df_list, ignore_index=True)    #create the dataframe journalSelfCitDf by concatenating all the dataframes contained in df_list

        all_journal_sc = []
        for idx, row in journalSelfCitDf.iterrows():    #for each dataframe row, create a corresponding JournalSelfCitation object having the same attributes
            journal_sc = JournalSelfCitation()
            journal_sc.creation = row["creation"]
            journal_sc.timespan = row["duration"]
            journal_sc.hasCitingEntity = self.getEntityById(row["citing"])  # convert the raw "citing" ID string into a fully instantiated BibliographicEntity object
            journal_sc.hasCitedEntity = self.getEntityById(row["cited"])    # convert the raw "cited" ID string into a fully instantiated BibliographicEntity object
            journal_sc.ids = [row["citation"]]

            all_journal_sc.append(journal_sc)   #the new JournalSelfCitation object is appended to the all_journal_sc list
        
        return all_journal_sc
    
    def getCitationsWithinTimespan(self, min_timespan: str, max_timespan: str) -> list[Citation]: 
        df_list = []
        for handler in self.citationQuery: 
            newDataFrame = handler.getCitationsWithinTimespan(min_timespan, max_timespan)   #NewDataFrame contains all the citations whose timespan falls between the min_timespan and the max_timespan in input
            df_list.append(newDataFrame)
        
        if not df_list: #if there were no dataframes and the df_list is therefore empty, the functions returns an empty list and won't try to concatenate an empty list of dataframe  
            return []
        
        CitTimespanDf = pd.concat(df_list, ignore_index=True)   #create the dataframe CitTimespanDf by concatenating all the dataframes contained in df_list

        all_citations_timespan = []
        for idx, row in CitTimespanDf.iterrows():   #for each dataframe row, create a corresponding Citation object having the same attributes
            citation = Citation() 
            citation.creation = row["creation"]
            citation.timespan = row["duration"]
            citation.ids = [row["citation"]]
            citation.hasCitingEntity = self.getEntityById(row["citing"])    # convert the raw "citing" ID string into a fully instantiated BibliographicEntity object
            citation.hasCitedEntity = self.getEntityById(row["cited"])      # convert the raw "cited" ID string into a fully instantiated BibliographicEntity object

            all_citations_timespan.append(citation)     #the new Citation object is appended to the all_citations_timespan list
        
        return all_citations_timespan

    def getBibliographicEntitiesWithinDate(self, start_date, end_date):
        df_list = [] 
        for handler in self.bibliographicEntityQuery:
            newDataFrame = handler.getBibliographicEntitiesWithinPublicationDate(start_date, end_date)   #NewDataFrame contains all the bib ent whose publication date falls between the start_date and end_date
            df_list.append(newDataFrame)        #append each dataframe to the initially empty df_list
                            
        if not df_list: #if there were no dataframes and the df_list is therefore empty, the functions returns an empty list and won't try to concatenate an empty list of dataframe  
            return []
        
        bibEntWithinDate = pd.concat(df_list, ignore_index=True)     #create the dataframe bibEntWithinDate by concatenating all the dataframes contained in df_list

        all_bib_ent_date = []
        for idx, row in bibEntWithinDate.iterrows():    #for each dataframe row, create a corresponding BibliographicEntity object having the same attributes values contained in the row
            bibEnt = BibliographicEntity() 
            bibEnt.title = row["title"]
            bibEnt.authors = [row["authors"]]
            bibEnt.pub_date = row["pub_date"]
            bibEnt.venue = row["venue"]
            bibEnt.ids = [row["ids"]] 

            all_bib_ent_date.append(bibEnt)     #the new bibliographic entity object is appended to the all_bib_ent_date list
        
        return all_bib_ent_date

    
    def getCitationsWithinDate(self, start_date: str, end_date: str) -> list[Citation]:
        df_list = [] 
        for handler in self.citationQuery:
            newDataFrame = handler.getCitationsWithinDate(start_date, end_date)   #NewDataFrame contains all the citations whose creation falls between the start_date and end_date 
            df_list.append(newDataFrame)        #append each dataframe to the initially empty df_list
                            
        if not df_list: #if there were no dataframes and the df_list is therefore empty, the functions returns an empty list and won't try to concatenate an empty list of dataframe  
            return []
        
        citationWithinDate = pd.concat(df_list, ignore_index=True)     #create the dataframe citationWithinDate by concatenating all the dataframes contained in df_list

        all_cit_date = []
        for idx, row in citationWithinDate.iterrows():  #for each dataframe row, create a corresponding Citation object having the same attributes
            citation = Citation() 
            citation.creation = row["creation"]
            citation.timespan = row["duration"]
            citation.ids = [row["citation"]]
            citation.hasCitingEntity = self.getEntityById(row["citing"])    # convert the raw "citing" ID string into a fully instantiated BibliographicEntity object
            citation.hasCitedEntity = self.getEntityById(row["cited"])  # convert the raw "cited" ID string into a fully instantiated BibliographicEntity object

            all_cit_date.append(citation)
        
        return all_cit_date 

class FullQueryEngine(BasicQueryEngine): #let's use a combination of the methods I've implemented 
    
    def __init__(self):
        super().__init__() #this "calls" the init of the superclass

    def getAuthorSelfCitationsByName(self, author_name: str) -> list[AuthorSelfCitation]:
        all_author_sc = self.getAllAuthorSelfCitations() # get all author self-citations using the base method
        result = []
        for citation in all_author_sc:  # loop through all self-citations and check if the given author appears in both citing and cited entities
            citing_ent = citation.getCitingEntity()
            cited_ent = citation.getCitedEntity()
            if citing_ent is not None and cited_ent is not None:
                citing_authors = citing_ent.getAuthors()
                cited_authors = cited_ent.getAuthors()

                if author_name in citing_authors and author_name in cited_authors: #if the author appears in both citing and cited entity, the citation is appended to the result list
                    result.append(citation)

        return result

    def getJournalSelfCitationsByName(self, journal_name: str) -> list[JournalSelfCitation]:
        all_journal_sc = self.getAllJournalSelfCitations()  # retrieve all journal self-citations using the base method
        result = []
        for citation in all_journal_sc: # loop through all self-citations and check if the given journal appears in both citing and cited entities
            citing_ent = citation.getCitingEntity()
            cited_ent = citation.getCitedEntity()
            if citing_ent is not None and cited_ent is not None:
                citing_journal = citing_ent.getVenue()
                cited_journal =  cited_ent.getVenue()

                if journal_name == citing_journal and journal_name == cited_journal:    #if the journal appears as venue in both citing and cited entity, the citation is appended to the result list

                    result.append(citation)

        return result


    def getCitationsOfBibEntityByTitleWithinDate(self, bib_entity_title: str, min_date: str, max_date: str) -> list[Citation]:
        all_citations = self.getAllCitations()  # first, collect all available citations using the base method
        result = []

        for citation in all_citations:  # filter citations by matching the cited entity's title (substring) and verifying the publication date bounds
            cited = citation.getCitedEntity()
            if cited is not None:
                cited_title = cited.getTitle()

                if bib_entity_title.lower() in cited_title.lower():
                    cited_date = cited.getPublicationDate()
                    if cited_date <= max_date and cited_date >= min_date:
                        result.append(citation)     #if the citation matches all the parametres in input, it is appended to the result list
        
        return result

    
    def getReferencesOfBibEntityByTitleWithinTimespan(self, bib_entity_title: str, min_timespan: str, max_timespan: str) -> list[Citation]:
        citations_within_timespan = self.getCitationsWithinTimespan(min_timespan, max_timespan)     # fetch citations that strictly fall within the required timespan
        result = []

        for citation in citations_within_timespan:  # check if the citing entity contains the specified title keyword
            citing = citation.getCitingEntity()
            if citing is not None:
                citing_title = citing.getTitle()

                if bib_entity_title.lower() in citing_title.lower():    
                    result.append(citation)         #if the citation matches all the parametres in input, it is appended to the result list
        
        return result