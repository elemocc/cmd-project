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
    
    #DA FINIRE
    def getBibliographicEntitiesWithTitle(self, title):
        bibEntWithAuthor = pd.DataFrame
        df_list = [] 
        for handler in self.bibliographicEntityQuery:
            newDataFrame = handler.getBibliographicEntitiesWithAuthor()   
            df_list.append(newDataFrame)        #append each dataframe to the initially empty df_list
                            
        if not df_list: #if there were no dataframes and the df_list is therefore empty, the functions returns an empty list and won't try to concatenate an empty list of dataframe  
            return []