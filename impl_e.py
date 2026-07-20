import pandas as pd
from classes import *

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

    def addCitationHandler(self, handler): #add the handler to the empty list creatd within the init   
        self.citationQuery.append(handler)
        return True 

    def addBibliographicEntityHandler(self, handler): #add the handler to the empty list creatd within the init
        self.bibliographicEntityQuery.append(handler)
        return True
    
    def getEntityById(self, id): #search for a specified ID among the citations and/or the bibliographic entities contained in the two databases
        matchingIdEnt = pd.DataFrame() #create an empty dataframe which will contain the possible matching bibliogrphic entity/citation returned by the handlers
        df_list = [] #create an empty list where to store the dataframes returne by the handlers
        for handler in self.bibliographicEntityQuery: #for each handler, ask the
            newDataFrame = handler.getById(id)
            df_list.append(newDataFrame)

        if  df_list: #controlla che la lista non sia vuota, nel caso per esempio in cui il method sia stato chiamato senza aver prima aggiunto gli handlers all'interno degli engines. se non è vuota concatena i dataframe        
            matchingIdEnt = pd.concat(df_list, ignore_index=True)

        if not matchingIdEnt.empty: #controlla che il dataframe non sia vuoto, solo se non è vuoto procede
            row = matchingIdEnt.iloc[0] #iloc prende direttamente la prima row (indice 0), visto che dovrebbe essere solo una la riga nel df
            
            bibEntWithId = BibliographicEntity()
            bibEntWithId.title = row["title"]
            bibEntWithId.authors = [row["author"]]
            bibEntWithId.pub_date = row["pub_date"]
            bibEntWithId.venue = row["venue"]
            bibEntWithId.ids = [row["id"]]

            return bibEntWithId
        
        else:
            matchingIdCit = pd.DataFrame()
            df_list = []
            for handler in self.citationQuery:
                newDataFrame = handler.getById(id)
                df_list.append(newDataFrame)
            
            matchingIdCit = pd.concat(df_list, ignore_index=True)
            
            if not matchingIdCit.empty: #controlla che il dataframe non sia vuoto, solo se non è vuoto procede
                row = matchingIdCit.iloc[0]
                if row["journal_sc"] == "yes":   #VERIFICARE CHE ALICE ABBIA TRATTATO LA JOURNAL SC IN QUESTO MODO
                    citWithId = JournalSelfCitation()
                
                elif row["author_sc"] == "yes":
                    citWithId = AuthorSelfCitation()
                
                else:
                    citWithId = Citation()
                
                citWithId.creation = row["creation"]
                citWithId.timespan = row["timespan"]
                citWithId.ids = [row["oci"]]
                citWithId.hasCitingEntity = self.getEntityById(row["citing"])
                citWithId.hasCitedEntity = self.getEntityById(row["cited"])
                                    
                
                return citWithId

        return None



    
    def getAllCitations(self):  #get all the citations from the handlers stored in the self.citationQuery list
        allCitations = pd.DataFrame()   #create a new empy dataframe where to store all the dataframe concatenated  
        df_list = []    #create an empty list which will contain all the dataframes from the handlers 
        for handler in self.citationQuery:  #iterate over the dataframe retriev by Silvia's handlers
            newDataFrame = handler.getAllCitations()   
            df_list.append(newDataFrame)        #append each dataframe to the initially empty df_list
        
        if not df_list: #if there were no dataframes and the df_list is therefore empty, the functions returns an empty list and won't try to concatenate an empty list of dataframe  
            return []
            

        allCitations = pd.concat(df_list, ignore_index=True)        #all the dataframe contained within the list will be concatenated in a single  dataframe
        
        all_citations = []
        for idx, row in allCitations.iterrows():
            citation = Citation() #aggiunto manualmente uno a uno gli attributi dell'oggetto Citation visto che non accetta parametri
            citation.creation = row["creation"]
            citation.timespan = row["timespan"]
            citation.ids = [row["oci"]]
            citation.hasCitingEntity = self.getEntityById(row["citing"])
            citation.hasCitedEntity = self.getEntityById(row["cited"]) 

            all_citations.append(citation)
        
        return all_citations 
            
    def getAllBibliographicEntities(self):
        allBibEnt = pd.DataFrame()
        df_list = []
        for handler in self.bibliographicEntityQuery:
            newDataFrame = handler.getAllBibliographicEntities()   
            df_list.append(newDataFrame)        #append each dataframe to the initially empty df_list
                            
        if not df_list: #if there were no dataframes and the df_list is therefore empty, the functions returns an empty list and won't try to concatenate an empty list of dataframe  
            return []
        
        allBibEnt = pd.concat(df_list, ignore_index=True)        #all the dataframe contained within the list will be concatenated in a single  dataframe


        all_bib_ent = []
        for idx, row in allBibEnt.iterrows():
            bibEnt = BibliographicEntity() #aggiunto manualmente uno a uno gli attributi dell'oggetto BibliographicEntity visto che non accetta parametri
            bibEnt.title = row["title"]
            bibEnt.authors = [row["author"]]
            bibEnt.pub_date = row["pub_date"]
            bibEnt.venue = row["venue"]
            bibEnt.ids = [row["id"]] 

            all_bib_ent.append(bibEnt)
        
        return all_bib_ent 
    

    def getBibliographicEntitiesWithTitle(self, title):
        df_list = [] 
        for handler in self.bibliographicEntityQuery:
            newDataFrame = handler.getBibliographicEntitiesWithTitle(title)   #NewDataFrame contains all the bib ent matching with the specified title
            df_list.append(newDataFrame)        #append each dataframe to the initially empty df_list
                            
        if not df_list: #if there were no dataframes and the df_list is therefore empty, the functions returns an empty list and won't try to concatenate an empty list of dataframe  
            return []
        
        bibEntWithTitle = pd.concat(df_list, ignore_index=True)     #create the a dataframe bibEntWithTitle by concatenating all the dataframes contained in df_list

        all_bib_ent_title = []
        for idx, row in bibEntWithTitle.iterrows(): #the for loop iterates over the dataframe creating new BibliographicEntity() objects and appending them to the list that will be return at the end
            bibEnt = BibliographicEntity() #aggiunto manualmente uno a uno gli attributi dell'oggetto BibliographicEntity visto che non accetta parametri
            bibEnt.title = row["title"]
            bibEnt.authors = [row["author"]]
            bibEnt.pub_date = row["pub_date"]
            bibEnt.venue = row["venue"]
            bibEnt.ids = [row["id"]] 

            all_bib_ent_title.append(bibEnt)
        
        return all_bib_ent_title           
    
    
    def getBibliographicEntitiesWithAuthor(self, author):
        df_list = [] 
        for handler in self.bibliographicEntityQuery:
            newDataFrame = handler.getBibliographicEntitiesWithAuthor(author)   #NewDataFrame contains all the bib ent matching with the specified author
            df_list.append(newDataFrame)        #append each dataframe to the initially empty df_list
                            
        if not df_list: #if there were no dataframes and the df_list is therefore empty, the functions returns an empty list and won't try to concatenate an empty list of dataframe  
            return []
        
        bibEntWithAuthor = pd.concat(df_list, ignore_index=True)     #create the a dataframe bibEntWithTitle by concatenating all the dataframes contained in df_list

        all_bib_ent_title = []
        for idx, row in bibEntWithAuthor.iterrows(): #the for loop iterates over the dataframe creating new BibliographicEntity() objects and appending them to the list that will be return at the end
            bibEnt = BibliographicEntity() #aggiunto manualmente uno a uno gli attributi dell'oggetto BibliographicEntity visto che non accetta parametri
            bibEnt.title = row["title"]
            bibEnt.authors = [row["author"]]
            bibEnt.pub_date = row["pub_date"]
            bibEnt.venue = row["venue"]
            bibEnt.ids = [row["id"]] 

            all_bib_ent_title.append(bibEnt)
        
        return all_bib_ent_title
    
    def getBibliographicEntitiesWithVenue(self, venue):
        df_list = [] 
        for handler in self.bibliographicEntityQuery:
            newDataFrame = handler.getBibliographicEntitiesWithVenue(venue)   #NewDataFrame contains all the bib ent matching with the specified author
            df_list.append(newDataFrame)        #append each dataframe to the initially empty df_list
                            
        if not df_list: #if there were no dataframes and the df_list is therefore empty, the functions returns an empty list and won't try to concatenate an empty list of dataframe  
            return []
        
        bibEntWithVenue = pd.concat(df_list, ignore_index=True)     #create the a dataframe bibEntWithTitle by concatenating all the dataframes contained in df_list

        all_bib_ent_venue = []
        for idx, row in bibEntWithVenue.iterrows(): #the for loop iterates over the dataframe creating new BibliographicEntity() objects and appending them to the list that will be return at the end
            bibEnt = BibliographicEntity() #aggiunto manualmente uno a uno gli attributi dell'oggetto BibliographicEntity visto che non accetta parametri
            bibEnt.title = row["title"]
            bibEnt.authors = [row["author"]]
            bibEnt.pub_date = row["pub_date"]
            bibEnt.venue = row["venue"]
            bibEnt.ids = [row["id"]] 

            all_bib_ent_venue.append(bibEnt)
        
        return all_bib_ent_venue
    
    def getAllAuthorSelfCitations(self):
        df_list = []
        for handler in self.citationQuery:
            newDataFrame = handler.getAllAuthorSelfCitations()
            df_list.append(newDataFrame)
        
        if not df_list: #if there were no dataframes and the df_list is therefore empty, the functions returns an empty list and won't try to concatenate an empty list of dataframe  
            return []
        
        authorSelfCitDf = pd.concat(df_list, ignore_index=True) 

        all_author_sc = []
        for idx, row in authorSelfCitDf.iterrows():
            author_sc = AuthorSelfCitation()
            author_sc.creation = row["creation"]
            author_sc.timespan = row["timespan"]
            author_sc.hasCitingEntity = self.getEntityById(row["citing"])
            author_sc.hasCitedEntity = self.getEntityById(row["cited"])
            author_sc.ids = [row["oci"]]

            all_author_sc.append(author_sc)
        
        return all_author_sc
    
    def getAllJournalSelfCitations(self):
        df_list = []
        for handler in self.citationQuery:
            newDataFrame = handler.getAllJournalSelfCitations()
            df_list.append(newDataFrame)
        
        if not df_list: #if there were no dataframes and the df_list is therefore empty, the functions returns an empty list and won't try to concatenate an empty list of dataframe  
            return []
        
        journalSelfCitDf = pd.concat(df_list, ignore_index=True) 

        all_journal_sc = []
        for idx, row in journalSelfCitDf.iterrows():
            journal_sc = JournalSelfCitation()
            journal_sc.creation = row["creation"]
            journal_sc.timespan = row["timespan"]
            journal_sc.hasCitingEntity = self.getEntityById(row["citing"])
            journal_sc.hasCitedEntity = self.getEntityById(row["cited"])
            journal_sc.ids = [row["oci"]]

            all_journal_sc.append(journal_sc)
        
        return all_journal_sc
    
    def getCitationsWithinTimespan(self, min_timespan, max_timespan): #CONTROLLARE PER CITED E CITING, SISTEMARE CODICE
        df_list = []
        for handler in self.citationQuery: 
            newDataFrame = handler.getCitationsWithinTimespan(min_timespan, max_timespan)
            df_list.append(newDataFrame)
        
        if not df_list: #if there were no dataframes and the df_list is therefore empty, the functions returns an empty list and won't try to concatenate an empty list of dataframe  
            return []
        
        CitTimespanDf = pd.concat(df_list, ignore_index=True) 

        all_citations_timespan = []
        for idx, row in CitTimespanDf.iterrows():
            citation = Citation() #aggiunto manualmente uno a uno gli attributi dell'oggetto Citation visto che non accetta parametri
            citation.creation = row["creation"]
            citation.timespan = row["timespan"]
            citation.ids = [row["oci"]]
            citation.hasCitingEntity = self.getEntityById(row["citing"])
            citation.hasCitedEntity = self.getEntityById(row["cited"])

            all_citations_timespan.append(citation)
        
        return all_citations_timespan

    def getBibliographicEntitiesWithinDate(self, start_date, end_date):
        df_list = [] 
        for handler in self.bibliographicEntityQuery:
            newDataFrame = handler.getBibliographicEntitiesWithinPublicationDate(start_date, end_date)   #NewDataFrame contains all the bib ent matching with the specified author
            df_list.append(newDataFrame)        #append each dataframe to the initially empty df_list
                            
        if not df_list: #if there were no dataframes and the df_list is therefore empty, the functions returns an empty list and won't try to concatenate an empty list of dataframe  
            return []
        
        bibEntWithinDate = pd.concat(df_list, ignore_index=True)     #create the a dataframe bibEntWithTitle by concatenating all the dataframes contained in df_list

        all_bib_ent_date = []
        for idx, row in bibEntWithinDate.iterrows(): #the for loop iterates over the dataframe creating new BibliographicEntity() objects and appending them to the list that will be return at the end
            bibEnt = BibliographicEntity() #aggiunto manualmente uno a uno gli attributi dell'oggetto BibliographicEntity visto che non accetta parametri
            bibEnt.title = row["title"]
            bibEnt.authors = [row["author"]]
            bibEnt.pub_date = row["pub_date"]
            bibEnt.venue = row["venue"]
            bibEnt.ids = [row["id"]] 

            all_bib_ent_date.append(bibEnt)
        
        return all_bib_ent_date

    
    def getCitationsWithinDate(self, start_date, end_date):
        df_list = [] 
        for handler in self.citationQuery:
            newDataFrame = handler.getCitationsWithinDate(start_date, end_date)   #NewDataFrame contains all the bib ent matching with the specified author
            df_list.append(newDataFrame)        #append each dataframe to the initially empty df_list
                            
        if not df_list: #if there were no dataframes and the df_list is therefore empty, the functions returns an empty list and won't try to concatenate an empty list of dataframe  
            return []
        
        citationWithinDate = pd.concat(df_list, ignore_index=True)     #create the a dataframe bibEntWithTitle by concatenating all the dataframes contained in df_list

        all_cit_date = []
        for idx, row in citationWithinDate.iterrows():
            citation = Citation() #aggiunto manualmente uno a uno gli attributi dell'oggetto Citation visto che non accetta parametri
            citation.creation = row["creation"]
            citation.timespan = row["timespan"]
            citation.ids = [row["oci"]]
            citation.hasCitingEntity = self.getEntityById(row["citing"])
            citation.hasCitedEntity = self.getEntityById(row["cited"]) 

            all_cit_date.append(citation)
        
        return all_cit_date 

class FullQueryEngine(BasicQueryEngine): #let's use a combination of the methods I've implemented 
    
    def __init__(self):
        super().__init__() #this "calls" the init of the superclass

    def getAuthorSelfCitationsByName(self, author_name):
        all_author_sc = self.getAllAuthorSelfCitations()
        result = []
        for citation in all_author_sc:
            citing_ent = citation.getCitingEntity()
            cited_ent = citation.getCitedEntity()
            if citing_ent is not None and cited_ent is not None:
                citing_authors = citing_ent.getAuthors()
                cited_authors = cited_ent.getAuthors()

                if author_name in citing_authors and author_name in cited_authors:
                    result.append(citation)

        return result

    def getJournalSelfCitationsByName(self, journal_name):
        all_journal_sc = self.getAllJournalSelfCitations()
        result = []
        for citation in all_journal_sc:
            citing_ent = citation.getCitingEntity()
            cited_ent = citation.getCitedEntity()
            if citing_ent is not None and cited_ent is not None:
                citing_journal = citing_ent.getVenue()
                cited_journal =  cited_ent.getVenue()

                if journal_name == citing_journal and journal_name == cited_journal:

                    result.append(citation)

        return result


    def getCitationsOfBibEntityByTitleWithinDate(self, bib_entity_title, min_date, max_date):
        all_citations = self.getAllCitations()
        result = []

        for citation in all_citations:
            cited = citation.getCitedEntity()
            if cited is not None:
                cited_title = cited.getTitle()

                if bib_entity_title.lower() in cited_title.lower():
                    cited_date = cited.getPublicationDate()
                    if cited_date <= max_date and cited_date >= min_date:
                        result.append(citation)
        
        return result

    
    def getReferencesOfBibEntityByTitleWithinTimespan(self, bib_entity_title, min_timespan, max_timespan):
        citations_within_timespan = self.getCitationsWithinTimespan(min_timespan, max_timespan)
        result = []

        for citation in citations_within_timespan:
            citing = citation.getCitingEntity()
            if citing is not None:
                citing_title = citing.getTitle()

                if bib_entity_title.lower() in citing_title.lower():
                    result.append(citation)
        
        return result

