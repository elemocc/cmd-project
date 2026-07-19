import pandas as pd
# Importiamo il tuo motore dal file in cui lo hai salvato
# Sostituisci "impl_e" con il nome esatto del tuo file senza il ".py"
from impl_e import FullQueryEngine 

# ==========================================
# 1. I TOY DATASET (Dati fittizi)
# ==========================================

# 1. Creare il DataFrame dal file CSV delle citazioni
mock_cit_df = pd.read_csv("data/dh_citations_rid.csv")

# 2. Creare il DataFrame dal file JSON delle entità bibliografiche
mock_bib_df = pd.read_json("data/dh_metadata_rid.json")

# Se vuoi stampare le prime 5 righe per verificare che sia tutto caricato correttamente:
# print("Anteprima Entità Bibliografiche:")
# print(mock_bib_df.head())

# print("\nAnteprima Citazioni:")
# print(mock_cit_df.head())


# ==========================================
# 2. I MOCK HANDLERS (Completi per tutti i metodi)
# ==========================================
class MockBibliographicHandler:
    def getById(self, id):
        # Cerca all'interno della lista di ID
        return mock_bib_df[mock_bib_df["id"].apply(lambda x: id in x if isinstance(x, list) else False)]
        
    def getAllBibliographicEntities(self):
        return mock_bib_df

    def getBibliographicEntitiesWithTitle(self, title):
        # Ricerca case-insensitive (ignorando le maiuscole/minuscole)
        # Il fillna(False) serve per evitare errori se ci sono valori nulli
        return mock_bib_df[mock_bib_df["title"].str.lower().str.contains(title.lower(), na=False)]
    
    def getBibliographicEntitiesWithAuthor(self, author):
        # Trasforma tutto in minuscolo e controlla se la stringa 'author' 
        # è contenuta in ALMENO UNO (any) degli elementi della lista di autori
        return mock_bib_df[mock_bib_df["author"].apply(
            lambda x: any(author.lower() in a.lower() for a in x) if isinstance(x, list) else False
        )]
    def getBibliographicEntitiesWithVenue(self, venue):
        return mock_bib_df[mock_bib_df["venue"].str.lower() == venue.lower()]
    
    def getBibliographicEntitiesWithinPublicationDate(self, start_date, end_date):
        # Una semplice comparazione alfabetica funziona benissimo per le stringhe ISO come "2020-01-01"
        return mock_bib_df[(mock_bib_df["pub_date"] >= start_date) & (mock_bib_df["pub_date"] <= end_date)]


class MockCitationHandler:
    def getById(self, id):
        return mock_cit_df[mock_cit_df["oci"] == id]
        
    def getAllCitations(self):
        return mock_cit_df
        
    def getAllAuthorSelfCitations(self):
        return mock_cit_df[mock_cit_df["author_sc"] == "yes"]
    
    def getAllJournalSelfCitations(self):
        return mock_cit_df[mock_cit_df["journal_sc"] == "yes"]
    
    def getCitationsWithinTimespan(self, min_timespan, max_timespan):
        # NOTA: Calcolare esattamente la differenza logica tra periodi come "P1Y5M" in Pandas puro 
        # richiede librerie complesse. Dato che è solo un test, per fare girare i tuoi loop 
        # restituiamo semplicemente le citazioni che hanno un timespan valorizzato (non nullo).
        return mock_cit_df[mock_cit_df["timespan"].notna()]
    
    def getCitationsWithinDate(self, start_date, end_date):
        # Stessa logica delle entità bibliografiche
        return mock_cit_df[(mock_cit_df["creation"] >= start_date) & (mock_cit_df["creation"] <= end_date)]

# ==========================================
# 3. IL TEST SUI DATI REALI
# ==========================================
def run_test():
    print("Inizializzo il FullQueryEngine...")
    que = FullQueryEngine()
    
    print("Aggiungo gli handler...")
    engine.addBibliographicEntityHandler(MockBibliographicHandler())
    engine.addCitationHandler(MockCitationHandler())
    
    print("\n" + "="*40)
    print(" 1. TEST: getEntityById('openalex:W3193297707')")
    print("="*40)
    ent = engine.getEntityById("0605199786-061301437736") #!
    if ent:
        print(f"Trovato! Titolo: | ID: {ent.ids}")
    else:
        print("Nessuna entità trovata con questo ID.")

    print("\n" + "="*40)
    print(" 2. TEST: getAllCitations")
    print("="*40)
    tutte_citazioni = engine.getAllCitations()
    print(f"Totale citazioni trovate: {len(tutte_citazioni)}")
    print("Ecco le prime 3:")
    for cit in tutte_citazioni[:3]: # Mostriamo solo le prime 3
        # Gestiamo il caso in cui l'entità citante/citata potrebbe essere None
        citing_id = cit.hasCitingEntity.ids[0] if cit.hasCitingEntity else "Sconosciuto"
        cited_id = cit.hasCitedEntity.ids[0] if cit.hasCitedEntity else "Sconosciuto"
        print(f" -> Citazione [{cit.ids[0]}]: {citing_id} cita {cited_id} (Creata il: {cit.creation})")

    print("\n" + "="*40)
    print(" 3. TEST: getAllBibliographicEntities")
    print("="*40)
    tutte_entita = engine.getAllBibliographicEntities()
    print(f"Totale entità trovate: {len(tutte_entita)}")
    print("Ecco le prime 3:")
    for e in tutte_entita[:3]:
        print(f" -> Titolo: '{e.title}' | Autori: {e.authors}")

    print("\n" + "="*40)
    print(" 4. TEST: getBibliographicEntitiesWithAuthor('Marras')")
    print("="*40)
    entita_marras = engine.getBibliographicEntitiesWithAuthor("Marras")
    if not entita_marras:
        print("Nessun articolo trovato per questo autore.")
    for e in entita_marras:
        print(f" -> Trovato: '{e.title}' | Data: {e.pub_date}")

    print("\n" + "="*40)
    print(" 5. TEST: getBibliographicEntitiesWithVenue('Colloquia Humanistica')")
    print("="*40)
    entita_venue = engine.getBibliographicEntitiesWithVenue("Colloquia Humanistica")
    for e in entita_venue:
        print(f" -> Trovato: '{e.title}' | Autori: {e.authors}")

    print("\n" + "="*40)
    print(" 6. TEST: Self Citations (Author & Journal)")
    print("="*40)
    author_sc = engine.getAllAuthorSelfCitations()
    journal_sc = engine.getAllJournalSelfCitations()
    print(f" -> Trovate {len(author_sc)} Author Self Citations.")
    print(f" -> Trovate {len(journal_sc)} Journal Self Citations.")

    print("\n" + "="*40)
    print(" 7. TEST: getCitationsWithinTimespan('P2Y', 'P3Y')")
    print("="*40)
    cit_timespan = engine.getCitationsWithinTimespan("P2Y", "P3Y")
    print(f" -> Trovate {len(cit_timespan)} citazioni in questo span temporale.")

    print("\n" + "="*40)
    print(" 8. TEST: Date Filters (Entità e Citazioni)")
    print("="*40)
    ent_date = engine.getBibliographicEntitiesWithinDate("2022-12", "2025-08")
    print(f"Entità tra 2022-12 e 2025-08 ({len(ent_date)} trovate):")
    for e in ent_date:
        print(f" -> '{e.title}' (Pubblicato: {e.pub_date})")

    cit_date = engine.getCitationsWithinDate("2024-12", "2025-08")
    print(f"\nCitazioni tra 2024-12 e 2025-08 ({len(cit_date)} trovate):")
    for c in cit_date:
        print(f" -> Citazione ID: {c.ids[0]} | Creata il: {c.creation}")
    





if __name__ == "__main__":
    run_test()