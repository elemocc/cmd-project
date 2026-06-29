from sqlite3 import connect
import json
import pandas as pd


#legge il file json
with open("data/dh_metadata.json", "r", encoding = "utf-8") as f:
    bib_data = json.load(f)

#crea un dataframe pandas con i dati presenti nel file json
bib_df = pd.DataFrame(bib_data)

#creo una lista in cui inserire gli ids interni delle pub_entities 
internal_id =[]

for idx, row in bib_df.iterrows():
    internal_id.append("pub-"+ str(idx))

#aggiungo la lista di id interni come colonna del dataframe, in posizione 0
bib_df.insert(0, "internal_id", pd.Series(internal_id, dtype= "string"))

#creo tre tabelle, una con gli attributi a valore singolo, una con gli ids e una con gli autori associati agli id
#prima tabella, a partire da bib_df contenente gli id interni, il titolo, data di pubblicazione e venue
publication_table =  bib_df[["internal_id","title", "pub_date", "venue"]]

#seconda tabella, contenente gli internal ids, corrispondenti ai vari id già associati 
publication_id