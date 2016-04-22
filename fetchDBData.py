import sqlite3
from itertools import groupby, chain
from mainDB import CTCPhotoDB

##################################
# parameters you shouldn't touch too often
##################################
# insert the database name
filename = "data/LightroomCatalog.lrcat"
# database tables were we will perform the search
dbTableCaptions = "AgLibraryIPTC"
dbTableImages = "AgLibraryCollectionImage"
dbTableFiles = "AgLibraryFile"
dbTableCollections = "AgLibraryCollection"
dbTableAdobeImages = "Adobe_Images"
# collection we are working with
idCollection = "683635"  # this is the current collection for the Fencing example
idParentCollection = "683583"  # this is the collection that contains the whole system
# collection to exclude
idExclude = "671489"
# verbose level
ver = 0


##################################

## generate the array listCollections carrying all of the collections
## that belong to our general export action. This operation is done taking
## the id of the parent collection as a reference
def getCollections(cursor):
    # get the information from the table with the collections
    command = "SELECT id_local,name FROM " + dbTableCollections + " WHERE parent LIKE '" + idParentCollection + "'"
    cursor.execute(command)
    res=[row for row in cursor]
    return res

##
def getImagesInSet(cursor, collection):
    command = "SELECT image, positionInCollection FROM " + dbTableImages + " WHERE collection LIKE '" + str(collection) + "'"
    cursor.execute(command)
    listImages=[row for row in cursor]
    return listImages

##
def getImgFiles(cursor, idImages):
    command = '''SELECT {0}.id_local, {1}.baseName, {2}.caption
    FROM {0}
    INNER JOIN {1}
    ON {0}.rootFile={1}.id_local
    INNER JOIN {2}
    ON {0}.id_local={2}.image
    WHERE {0}.id_local in ({3});
    '''.format(dbTableAdobeImages,dbTableFiles,dbTableCaptions,",".join(str(i) for i in idImages))
    cursor.execute(command)
    listFiles=[row for row in cursor]
    return listFiles

def combineLists(list1,list2):
    lst=sorted(chain(list1,list2),key=lambda x:x[0])
    resultList=[]
    for k,g in groupby(lst,key=lambda x:x[0]):
        d={}
        for dct in g:
            d.update(dct)
        d=dict((key,value) for key,value in d.iteritems() if key in ("id_local","baseName","caption","positionInCollection"))
        resultList.append(d)
    return resultList

def extractAndPopulate():
    photoDB=CTCPhotoDB()

    ## The Loop that will look into the DB
    with sqlite3.connect(filename) as conn:
        # Create a DB handler
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get the list of collections under a certain parent
        listCollections=getCollections(cursor)
        
        print "Begin!"
        # Get the information from the table with the images in the collections
        for collection in listCollections:
            print collection
            photoDB.addSet({"set_id":collection[0],"name":collection[1]})
            photoDB.commit();
            # Init the arrays to be used when navigating a collection
            # List of images
            listImages = []
            
            # Get the name of the set we are working with
            setName = collection[1]
            
            # Get the images in the set (populates listImages[])
            listImages=getImagesInSet(cursor, collection[0])
            print len(listImages)
            imgFiles=getImgFiles(cursor, [i[0] for i in listImages])

            resultList=combineLists(listImages,imgFiles)
            # Sort the list and add it to the global list
            resultList=sorted(resultList, key=lambda x: x["positionInCollection"])
            #print resultList
            
            '''
            if collection[0]==683635:
                print "###############"
                for one in resultList:
                    print one
                print "###############"
            '''
            #if collection[0]==683635:
            for idx, one in enumerate(resultList):
                photoDB.addPhoto({"ID":one["id_local"],"file_name":one["baseName"],"set_id":collection[0],"order_in_set":idx})
            photoDB.commit();
            ### Save the resultList into new db and do stuff

if __name__=="__main__":
    extractAndPopulate()