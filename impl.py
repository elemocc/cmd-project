

# Importa le classi degli oggetti
from classes import Citation, BibliographicEntity, AuthorSelfCitation, JournalSelfCitation

# Importa gli Handlers di Alice e Silvia
from handlers import (
    CitationUploadHandler, 
    BibliographicEntityUploadHandler, 
    CitationQueryHandler, 
    BibliographicEntityQueryHandler
)

# Importa i motori di ricerca
from basic_full_qe import BasicQueryEngine, FullQueryEngine