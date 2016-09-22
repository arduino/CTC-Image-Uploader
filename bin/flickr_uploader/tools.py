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

def deletePhotos(photos,doCommit=True):
	setsList=set()
	for one in photos:
		deletePhoto(one["photo_id"],False)
		setsList.add(one["set_id"])

	for set_id in setsList:
		set_id="'{}'".format(set_id)
		db.modifyRec("sets",{"set_id":set_id},{"shortlinked":0,"state":1})
		print "Set_id {} un-shortened".format(set_id)

	if doCommit:
		db.commit()



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

	deletePhotos(photos)

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

def flickrDeletePhotosByFilename(filename):
	try:
		res=f.photos.search(user_id="me",text=filename)
	except Exception as e:
		print e
	else:
		photos=res.find("photos").findall("photo")
		print res.find("photos").attrib["total"]
		for one in photos:
			photo_id=one.attrib["id"]
			f.photos.delete(photo_id=photo_id)
			print photo_id+"Deleted"

#
# Mark a photoset and all its photos as not shortlinked.
#
#
def markSetForShortLinks(set_id):
	photoSet=db.getSetByID(set_id)
	state=1 if photoSet["state"] == 2 else photoSet["state"]
	
	set_id="'{}'".format(set_id)
	db.modifyRec("sets",{"set_id":set_id},{"shortlinked":0,"state":state})
	db.modifyRec("photos",{"set_id":set_id},{"synced":"synced&3"})
	db.commit()

def markSetsForShortLinksByPhotoID(photo_id):
	cmd="""
	UPDATE sets
	SET shortlinked=0
	WHERE set_id IN
		(
		SELECT sets.set_id 
		FROM sets
		INNER JOIN photos
		ON sets.set_id==photos.set_id
		WHERE photos.photo_id=='{}'
		)
	""".format(photo_id)
	db.makeQuery(cmd)
	db.commit()

if __name__=="__main__":
	pass
	#db.cleanSetByID(683635).commit()
	#deletePhoto(823397)
	#deletePhotoSet("684603")
	#deleteAllPhotoSets()
	#flickrDeletePhotosetFully(1234)
	#flickrDeletePhotosByFilename("P9040276")
	markSetsForShortLinksByPhotoID("841850")