from pymongo import MongoClient
import json
import os
import pymongo


def openJsonFile():
    # opens a file with the filename fileName
    # used for json files

    fName = input("Enter name of json file you want open followed by .json: ")
    port = input("Enter port number: ")

    # Connect to the specifed port on localhost for the mongodb server.
    client = MongoClient("mongodb://localhost:" + port) 

    # Make the database 291db
    db = client["291db"]

    # Check if the collection already exists
    collist = db.list_collection_names()
    if "dblp" in collist:
        # Delete all the entries from the collection that were previously there
        print("Collection already exists, deleting previous entries.")
        col = db["dblp"]
        col.drop()
    
    else:
        db.create_collection("dblp")

    col = db["dblp"]
    
    # Use mongoimport to import all the data
    os.system("mongoimport --db 291db" +" --port="+ port + " --collection dblp --type=json --file="+fName)

    # Clustured index 
    col.update_many({},[{"$set":{"year":{"$toString":"$year"}}}])
    col.create_index([("title", pymongo.TEXT),
                           ("abstract", pymongo.TEXT),
                           ("authors", pymongo.TEXT),
                           ("venue", pymongo.TEXT),
                           ("year", pymongo.TEXT)],default_language="none")



openJsonFile()