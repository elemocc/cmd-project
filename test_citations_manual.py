import os
from upload_citation import CitationUploadHandler, CitationQueryHandler
from SPARQLWrapper import SPARQLWrapper, POST
import csv

# Namespace di default di Blazegraph (quello che si crea da solo al primo avvio)
ENDPOINT = "http://127.0.0.1:9999/blazegraph/namespace/kb/sparql"

# dh_citations.csv sta sul Desktop, mentre questo script sta 3 cartelle piu' in basso
# (Desktop/UniBo LM/py_module2/cmd_project/) -> usiamo il percorso "assoluto" verso il Desktop,
# cosi' funziona indipendentemente da dove lanci lo script
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")
FULL_CSV = os.path.join(DESKTOP_PATH, "dh_citations.csv")

# il CSV ridotto per i test veloci lo teniamo invece nella stessa cartella dello script
TEST_CSV = FULL_CSV  # usa il file completo invece di quello ridotto

def clear_graph():
    """Svuota il namespace 'kb' prima di ogni test, per ripartire da zero.
    IMPORTANTE: usalo solo su un namespace di test, mai su dati definitivi!"""
    sparql = SPARQLWrapper(ENDPOINT)
    sparql.setMethod(POST)
    sparql.setQuery("DELETE WHERE { ?s ?p ?o }")
    sparql.query()
    print("Grafo svuotato.\n")


def test_upload():
    print("=== TEST 1: Upload ===")
    handler = CitationUploadHandler()
    handler.setDbPathOrUrl(ENDPOINT)
    result = handler.pushDataToDb(TEST_CSV)
    assert result is True, "L'upload ha restituito False: controlla che Blazegraph sia acceso"
    print("Upload completato con successo.\n")


def test_get_all_citations():
    print("=== TEST 2: getAllCitations ===")
    handler = CitationQueryHandler()
    handler.setDbPathOrUrl(ENDPOINT)
    df = handler.getAllCitations()

    print(f"Righe trovate: {len(df)}")
    print(df.head())
    print(f"Colonne: {list(df.columns)}\n")

    assert len(df) > 0, "getAllCitations ha restituito un DataFrame vuoto!"
    assert "citation" in df.columns
    assert "citing" in df.columns
    assert "cited" in df.columns
    print("OK\n")


def test_self_citations():
    print("=== TEST 3: Author/Journal self-citations ===")
    handler = CitationQueryHandler()
    handler.setDbPathOrUrl(ENDPOINT)

    df_author = handler.getAllAuthorSelfCitations()
    df_journal = handler.getAllJournalSelfCitations()

    print(f"Author self-citations trovate: {len(df_author)}")
    print(f"Journal self-citations trovate: {len(df_journal)}")

    with open(TEST_CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    expected_author = sum(1 for r in rows if r["author_sc"].strip().lower() == "yes")
    expected_journal = sum(1 for r in rows if r["journal_sc"].strip().lower() == "yes")

    print(f"Attese dal CSV -> author: {expected_author}, journal: {expected_journal}")
    assert len(df_author) == expected_author, "Mismatch sulle author self-citations!"
    assert len(df_journal) == expected_journal, "Mismatch sulle journal self-citations!"
    print("OK\n")


def test_date_filter():
    print("=== TEST 4: getCitationsWithinDate ===")
    handler = CitationQueryHandler()
    handler.setDbPathOrUrl(ENDPOINT)

    df_all = handler.getAllCitations()
    df_filtered = handler.getCitationsWithinDate(min_date="2015-01-01", max_date="2020-01-01")

    print(f"Totale citazioni: {len(df_all)}, nel range: {len(df_filtered)}")
    assert len(df_filtered) <= len(df_all)
    print("OK\n")


def test_timespan_filter():
    print("=== TEST 5: getCitationsWithinTimespan ===")
    handler = CitationQueryHandler()
    handler.setDbPathOrUrl(ENDPOINT)

    df_filtered = handler.getCitationsWithinTimespan(min_span="P1Y", max_span="P5Y")
    print(f"Citazioni con durata tra 1 e 5 anni: {len(df_filtered)}")

    if not df_filtered.empty:
        assert df_filtered["days"].min() >= 365
        assert df_filtered["days"].max() <= 1825
    print("OK\n")

if __name__ == "__main__":
    print("Inizio: preparo il CSV di test...")
    print("CSV pronto. Ora svuoto il grafo...")
    clear_graph()
    print("Grafo svuotato. Ora faccio l'upload...")
    test_upload()
    print("Upload finito!")
    test_get_all_citations()
    test_self_citations()
    test_date_filter()
    test_timespan_filter()
    print("=== TUTTI I TEST SONO PASSATI ===")