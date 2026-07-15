# In this file are contained all the classes developed for the project. 

# 1: IdentifiableEntity. The class for entities identified by an ID.
# The method getIds allows one to retrieve the correct IDs from a list.
class IdentifiableEntity: 
    def __init__(self):
        self.ids = []

    def getIds(self) -> list[str]:
        return self.ids
    
# 2: BibliographicEntity. The class for bibliographic entities is a subclass of IdentifiableEntity.
# Besides, it has additional attribute methods for getting Title, Authors, PublicationDate, and Venue.
class BibliographicEntity(IdentifiableEntity): 
    def __init__(self):
        super().__init__()

        # Attributes
        self.title = ""
        self.authors = []
        self.pub_date = ""
        self.venue = ""

    # Methods
    def getTitle(self) -> str:
        return self.title

    def getAuthors(self) -> list[str]:
        return self.authors

    def getPublicationDate(self) -> str:
        return self.pub_date

    def getVenue(self) -> str:
        return self.venue
    
# 3: Citation. The class for citation refers to the relationship between two bibliographic entities. 
# It is a subclass of IdentifiableEntity. Besides, it has additional attributes and methods for 
# Creation, Timespan, Citing entity, and Cited entity. 
class Citation(IdentifiableEntity): 
    def __init__(self):
        super().__init__()

        # Attributes
        self.creation = ""
        self.timespan = ""
        self.hasCitingEntity = None
        self.hasCitedEntity = None


    # Methods
    def getCreation(self) -> str:
        return self.creation
    
    def getTimespan(self) -> str:
        return self.timespan
    
    def getCitingEntity(self) -> BibliographicEntity:
        return self.hasCitingEntity
    
    def getCitedEntity(self) -> BibliographicEntity:
        return self.hasCitedEntity

# 4: JournalSelfCitation. The subclass of Citation for journal self-citation in which
# the citing and cited entities are the same journal. It does not have any additional attributes or methods.
class JournalSelfCitation(Citation): 
    def __init__(self):
        super().__init__()

# 5: AuthorSelfCitation. The subclass of Citation for author self-citation, in which
# the citing and cited entities share at least one author. It does not have any additional attributes or methods. 
class AuthorSelfCitation(Citation): 
    def __init__(self):
        super().__init__()


