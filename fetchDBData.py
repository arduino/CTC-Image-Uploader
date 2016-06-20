import sqlite3
import os,sys
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

dbPath="maindb.db"
tmpdbPath="maindb_old.db"

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

def getBoardVersion(caption):
    versions=caption.split("**")[1]
    return versions

def extractAndPopulate(photoDB):

    ## The Loop that will look into the DB
    with sqlite3.connect(filename) as conn:
        # Create a DB handler
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get the list of collections under a certain parent
        listCollections=getCollections(cursor)
        
        # Get the information from the table with the images in the collections
        auto_id=0
        for collection in listCollections:
            print collection
            photoDB.addSet({"set_id":collection[0],"name":collection[1]})
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
                board_version=getBoardVersion(one["caption"])
                photoDB.addPhoto({"ID":auto_id,"photo_id":one["id_local"],"file_name":one["baseName"],"set_id":collection[0],"order_in_set":idx,"board_version":board_version})
                auto_id=auto_id+1
        photoDB.commit();
            ### Save the resultList into new db and do stuff

def updateDB(photoDB, oldDBPath):
    cur=photoDB.conn.cursor()
    cur.execute('ATTACH DATABASE "{}" AS db2'.format(oldDBPath))
    #cur.execute('SELECT db2.photos.folder, main.photos.photo_id FROM db2.photos INNER JOIN main.photos WHERE db2.photos.synced==7')
    cmd=['''
        UPDATE main.photos
        SET synced=(
                SELECT synced FROM db2.photos 
                WHERE photo_id=main.photos.photo_id AND set_id=main.photos.set_id),
            folder=(
                SELECT folder FROM db2.photos
                WHERE photo_id=main.photos.photo_id),
            hosted_url=(
                SELECT hosted_url FROM db2.photos
                WHERE photo_id=main.photos.photo_id),
            hosted_id=(
                SELECT hosted_id FROM db2.photos
                WHERE photo_id=main.photos.photo_id),
            refering_url=(
                SELECT refering_url FROM db2.photos
                WHERE photo_id=main.photos.photo_id)
    ''',
    '''
        UPDATE main.sets
        SET hosted_id=(
            SELECT hosted_id FROM db2.sets
            WHERE set_id=main.sets.set_id),
            state=(
            SELECT state!=0 FROM db2.sets
            WHERE set_id=main.sets.set_id)
    ''']
    
    cmd2=['''
        UPDATE photos
        SET folder="",hosted_url="",hosted_id="",refering_url=""
    ''',
    '''
        UPDATE sets
        SET hosted_id="",state=0
    ''']

    for one in cmd:
        cur.execute(one)

    photoDB.conn.commit()

if __name__=="__main__":
    print "Some data will be lost with this operation. \
    \nPress y to continue, other keys to quit."
    cfm=raw_input("")
    if cfm!="y":
        quit()

    if os.path.isfile(tmpdbPath):
        print tmpdbPath+" already exists. \
        \nRemove it manually if there's nothing important."
        quit()
    os.rename(dbPath,tmpdbPath)

    print "Creating tables..."
    photoDB=CTCPhotoDB()
    photoDB.createTables()
    photoDB.commit()

    print "Populating tables..."
    extractAndPopulate(photoDB)

    print "Updating tables with existing data..."
    updateDB(photoDB,tmpdbPath)
    
    print "Cleaning up..."
    photoDB.close()
    os.remove(tmpdbPath)

    print "All done."