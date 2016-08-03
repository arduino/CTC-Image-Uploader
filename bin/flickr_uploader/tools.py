import flickrapi
import threading, Queue
import time, os

from flickrapi.exceptions import FlickrError
from configs import flickr_api_key, flickr_api_secret
from mainDB import CTCPhotoDB


upload_queue=Queue.Queue()
upload_workers=[]

db_queue=Queue.Queue()

db=CTCPhotoDB()

f = flickrapi.FlickrAPI(flickr_api_key, flickr_api_secret)


#
# Delete a single photo from Flickr and keep it tracked in db
#
#
def deletePhotoInFlickr(flickrPhotoID):
	try:
		res=f.photos.delete(photo_id=flickrPhotoID)
	except FlickrError:
		print "photo "+flickrPhotoID+" gone"


def deletePhoto(photoID,doCommit=True):
	photo=db.getPhotoByID(photoID)
	if photo["hosted_id"]=="":
		return 

	deletePhotoInFlickr(photo["hosted_id"])

	db.cleanPhotoByID(photoID)
	if doCommit:
		db.commit()

	print "photo_id {} deleted".format(photoID)






#
# Delete all photos belonging to a set, and the set itself 
# from Flickr. And keep it tracked in db
#
#
def deletePhotoSetInFlickr(flickrAlbumID):
	try:
		f.photosets.delete(photoset_id=flickrAlbumID)
	except FlickrError:
		print "album "+flickrAlbumID+" gone"


def deletePhotoSet(photoSetID):
	photoSet=db.getSetByID(photoSetID)
	photos=db.getPhotosBySetID(photoSetID)

	if photoSet["hosted_id"]!="":
		deletePhotoSetInFlickr(photoSet["hosted_id"])
	else:
		print "photoSet {} is not hosted".format(photoSetID)

	for one in photos:
		deletePhoto(one["photo_id"],False)

	db.cleanSetByID(photoSetID).commit()

	print "set_id {} deleted".format(photoSetID)

def deleteAllPhotoSets():
	photoSets=db.getAllSets()

	for one in photoSets:
		deletePhotoSet(one["set_id"])

	print "All Deleted"




#
# Delete an untracked photoset and all its photos from flickr
#
#
def flickrDeletePhotosetFully(set_hosted_ID):
	try:
		res=f.photosets.getPhotos(photoset_id=set_hosted_ID)
	except Exception as e:
		print e
	else:
		photos=res.find("photoset").findall("photo")
		for one in photos:
			photo_id=one.attrib["id"]
			print photo_id
			f.photos.delete(photo_id=photo_id)

	try:
		f.photosets.delete(photoset_id=set_hosted_ID)
	except Exception as e:
		print e
	print "photoset {} deleted".format(set_hosted_ID)



#
# Mark a photoset and all its photos as not shortlinked.
#
#
def markSetForShorLinks(set_id):
	set_id="'{}'".format(set_id)
	db.modifyRec("sets",{"set_id":set_id},{"shortlinked":0})
	db.modifyRec("photos",{"set_id":set_id},{"synced":"synced&3"})
	db.commit()

if __name__=="__main__":
	pass
	#db.cleanSetByID(683635).commit()
	#deletePhoto(823397)
	#deletePhotoSet(683587)
	#deletePhotoSet(683696)
	#deleteAllPhotoSets()
	#flickrDeletePhotosetFully(1234)