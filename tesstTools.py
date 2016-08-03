import os
from shutil import copyfile
from bin.flickr_uploader import tools

def backupDB():
    copyfile("maindb.db","maindb_backup.db")

def cleanUpDBs():
    toRemove=["maindb.db","maindb_old.db"]

    for one in toRemove:
        try:
            os.remove(one)
        except OSError as e:
            print e

    copyfile("maindb_backup.db","maindb.db")

if __name__=="__main__":
    #backupDB()
    tools.markSetForShorLinks("684600")
    #raw_input("done...Enter to revert")
    #cleanUpDBs()