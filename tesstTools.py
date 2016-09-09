import os,sys
from shutil import copyfile
from bin.flickr_uploader import tools

def backupDB():
    copyfile("maindb.db","maindb_backup.db")

def recoverDB():
    copyfile("maindb_backup.db","maindb.db")

def cleanUpDBs():
    toRemove=["maindb.db","maindb_old.db"]

    for one in toRemove:
        try:
            os.remove(one)
        except OSError as e:
            print e

    copyfile("maindb_backup.db","maindb.db")

if __name__=="__main__":
    args=sys.argv

    if "--backup" in args:
        backupDB()
    elif "--recover" in args:
        recoverDB()
        
    #tools.markSetForShorLinks("684600")
    #raw_input("done...Enter to revert")
    #cleanUpDBs()