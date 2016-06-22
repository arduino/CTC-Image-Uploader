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


def deletePhotoInFlickr(flickrPhotoID):
	try:
		res=f.photos.delete(photo_id=flickrPhotoID)
	except FlickrError:
		print "photo "+flickrPhotoID+" gone"

def deletePhoto(photoID):
	cmd="""
	UPDATE photos
	SET synced=0, hosted_url='', refering_url='', hosted_id=''
	WHERE photo_id='{}'
	"""
	rec=db.getPhotoByID(photoID)
	deletePhotoInFlickr(rec["hosted_id"])

	db.makeQuery(cmd.format(photoID))
	db.commit()

	print "photo_id {} deleted".format(photoID)




def deletePhotoSetInFlickr(flickrAlbumID):
	try:
		f.photosets.delete(photoset_id=flickrAlbumID)
	except FlickrError:
		print "album "+flickrAlbumID+" gone"

def deletePhotoSet(photoSetID):
	cmd="""
	UPDATE sets
	SET state=0, hosted_id=''
	WHERE set_id='{}'
	"""
	photoSet=db.getSetByID(photoSetID)
	photos=db.getPhotosBySetID(photoSetID)

	deletePhotoSetInFlickr(photoSet["hosted_id"])
	db.makeQuery(cmd.format(photoSetID))
	db.commit()

	for one in photos:
		deletePhoto(one["photo_id"])

	print "set_id {} deleted".format(photoSetID)

if __name__=="__main__":
	pass
	#deletePhoto(823397)
	#deletePhotoSet(683622)
	#deletePhotoSet(683696)