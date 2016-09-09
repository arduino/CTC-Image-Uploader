import os 
from distutils.dir_util import copy_tree
from shutil import rmtree

from mainDB import CTCPhotoDB

from MainProcedure import processAll
from UploadPhotos import getFilenameFromRec
from tools import deletePhotos

db=CTCPhotoDB()


def updatePhotos(newFolder,oldFolder="./data/images/"):
	print "Updating photos... "
	if not os.path.isdir(newFolder):
		print "{} doesn't exist, nothing to update".format(newFolder)
		return 

	print "Cleaning up old photos"
	deleteOldPhotosFromNew(newFolder)

	print "Moving new photos to original folder"
	fileOperations(newFolder,oldFolder)

	processAll()



def deleteOldPhotosFromNew(folder):
	pics=db.getAllPhotos()
	res=[]
	for one in pics:
		filename=getFilenameFromRec(one,db,folder)
		if filename=="":
			continue

		res.append(one)

	print "Number of photos to be updates: ",len(res)

	deletePhotos(res,True)

def fileOperations(newFolder,oldFolder):
	copy_tree(newFolder,oldFolder)
	rmtree(newFolder)

if __name__=="__main__":
	updatePhotos("./data/images_new/")
	#cleanPhotosFromNew("./data/images_new/")
	#copyNewPhotosToFolder("./data/images_new/","./data/images_new2/")