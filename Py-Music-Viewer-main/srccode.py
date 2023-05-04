from pymongo import MongoClient
import json  
import os    
import pymongo  

global col, db, port

def startProgram():
    global col, db, port
    port = input("Enter port number: ")
    # Connect to the specifed port on localhost for the mongodb server.
    client = MongoClient("mongodb://localhost:" + port) 

    # Make the database 291db
    db = client["291db"]

    col = db["dblp"]


def displayAuthorSearchResult(result):

    keys = result.keys()
    resultStr = ""
    for key in keys:
        if key != "_id" and key != "authors" and key != "references" and key != "n_citation" and  key != "abstract":
            resultStr += str(key.capitalize()) + ": " + str(result[key])

def displayArticleSearchResult(result):

    keys = result.keys()
    resultStr = ""
    for key in keys:
        if key != "_id" and key != "authors" and key != "references" and key != "n_citation" and  key != "abstract":
            resultStr += str(key.capitalize()) + ": " + str(result[key]) + "|"
    
    return resultStr

def searchArticles():
    global col, db, port

    # Ask the user for keywords as input
    kwInput = input("Enter the keywords of article you want to find: ").lower()

    # Make the keywords into a list and make them unique (by turning them into a set)
    keywords = list(set(kwInput.split()))

    # doc=col.find({"$or":[{"$and":[{"title":"^.*the.*$"},{"title":"^.*and.*$"}]},{"$and":[{"author":"/.*the.*/"},{"author":"/.*and.*/"}]}]})
    
    #not working corectly 
    # articles_query_list=[]  
    # fields_list=["title","author","abstract","venue","year"]
    # for f in fields_list:
    #     w_list=[]
    #     for word in keywords:
    #         w_list.append({f: {"$regex": "^.*"+word+".*$"}})
    #     articles_query_list.append({"$and": w_list})

    # doc=col.find({"$or": articles_query_list},{"title":1,"year":1,"venue":1})
  
    kwModified = ' '.join("\"" + kw + "\"" for kw in keywords)
    print(kwModified)
    doc=col.find({"$text":{"$search": kwModified}})
    test = 0
 
    results = []
    
    i = 1
    for result in doc:
        results.append(result)
        print(str(i)+":", displayArticleSearchResult(result))
        i +=1
    print ("Select a result from above")
    selInput = input("Select an article from above by using it's number or press enter to exit: ")

    if selInput.isnumeric():

        if int(selInput) in range(1,len(results) + 1):
            selection = results[int(selInput) -1]

            # Display the extra information
            print("----------------------------------")
            print("Extra information:")
            for key in selection.keys():
                print(str(key).capitalize() + ":", selection[key])
            print("----------------------------------")
        else:
            print("Selection out of range. Exiting prompt.")
            return
    
    else:
        print("Exiting prompt.")
    
    return
    
    
def searchAuthors():
    global col, db, port

    # Ask the user for keywords as input
    kwInput = input("Enter the keywords of Authors you want to find: ").lower()

    # Make the keywords into a list and make them unique (by turning them into a set)
    keywords = list(set(kwInput.split()))

    w_list = []
    
    # Construct a regex for each word in the keywords

    if keywords:
        for word in keywords:
            w_list.append({"authors": {"$regex": "{}b".format(chr(92))+word+"{}b".format(chr(92)),"$options":"i"}})
    
    else:
        w_list.append({})

    # Construct the full query, since all keywords have to be included use $and. 
    # Note: the author array was unwinded so that the search will work by the individual 
    # elements in the array (samething with the grouping)

    # METHODS referenced from: https://stackoverflow.com/questions/21509045/mongodb-group-by-array-inner-elements

    query = [{"$unwind":"$authors"},{"$match":{"$and": w_list}},{"$group":{"_id":"$authors","count": { "$sum": 1 }}}]
    print(query)
    doc = col.aggregate(query)

    results = []
    i = 1
    for result in doc:
        results.append(result)
        print(str(i)+":", "Name:",result["_id"],"Number of Publications:",result["count"])
        i +=1
    
    print ("Select a result from above")
    selInput = input("Select an article from above by using it's number or press enter to exit: ")

    if selInput.isnumeric():

        if int(selInput) in range(1,len(results) + 1):
            selection = results[int(selInput) -1]
            # find all the articles by the author
            articles = col.aggregate([{"$match":{"authors":selection["_id"]}},{"$sort":{"year":-1}}])
            i = 1
            
            
            # Display the results 
            for article in articles:
                print
                print('Article', i)
                print('-----------------------------------------')
                for key in article.keys():
                    print(str(key).capitalize() + ":", article[key])
                print('-----------------------------------------')
                i += 1


        else:
            print("Selection out of range. Exiting prompt.")
            return
    
    else:
        print("Exiting prompt.")
    
    return
    

def addArticle():
    unique_id=input("Input a Unique ID: ")
    title=input("Input a Title: ")
    authors=input("Input a list of authors: ")
    authors_list=authors.split()
    year=input("Input a year: ")
    refrences=''
    n_citation=0

    id_search=col.find({"id":unique_id})
    
    results = []
    for i in id_search:
        results.append(i)
    if results == []:
        col.insert_one({"id":unique_id,"title":title,"authors":authors_list,"year":year,"abstract":"None","venue":"None","references":refrences,"n_citation":n_citation})
        print("Adding Succesfull")
        return True
    else:
        print("Id is not unique , Please try adding again with a unique ID")
        print("Adding Unsuccesfull")
        return False

def listVenues():
    uInput=input('Please enter a number to see the listing of top venues: ')

    if uInput.isnumeric():
        n = int(uInput)

        # Create an index for references
        col.create_index([("references", pymongo.DESCENDING)])

        query1 = [

            {"$lookup":
                {
                    "from":"dblp",
                    "localField":"id",
                    "foreignField":"references",
                    "as":"joinedV"
                }
            },
            # the joinedV contains all the articles that reference a particular article
            # Group by venue of each article, sort by the sum of the count of joinedV of each articles in the venue
            {
                "$group":{
                    "_id":"$venue",
                    "NumberOfArticlesReferencingVenue": {"$sum": {"$size":"$joinedV"}},
                    "NumberOfArticlesinVenue":{"$sum":1}
                }
            },
            {'$sort': {'NumberOfArticlesReferencingVenue': -1}},
            {"$limit":n}
        ]

        f=col.aggregate(query1)
        for i in f:
            if i["_id"] != "":
                print("Venue Name:",i["_id"],"Number of Articles Referencing Venue:",i["NumberOfArticlesReferencingVenue"],"Number of Articles in Venue:",i["NumberOfArticlesinVenue"])

    else:
        print("Invalid input, exiting prompt.")



def main():  
    startProgram()
    
    user_selection=""
    valid_options=["1","2","3","4","5"]
    while user_selection != "5":
        print("Welcome !! What would you like to do ?")
        print("Press 1 to Search for Articles")
        print("Press 2 to Search for Authors")
        print("Press 3 to List the Venues")
        print("Press 4 to Add an Article ")
        print("Press 5 to Exit the Program")
        print("\n")
        user_selection=input("")
        if(user_selection in valid_options):
            if user_selection=="1":
                searchArticles()
            if user_selection=="2":
                searchAuthors()
            if user_selection=="3":
                listVenues()
            if user_selection=="4":
                addArticle()
        else:
            print("Please Print a valid input")

    print("GoodBye!")

main()
        
        