#
#	synced value of photos:
# 0: unsynced 
# synced & 1 == 1: uploaded
# synced & 2 == 2: added to flickr set
# synced & 4 == 4: bitly link set
#
# state value of sets:
# 0: not created 
# 1: created
# 2: ordered
#

import sqlite3
import flickrapi

from configs import flickr_api_key, flickr_api_secret
from mainDB import CTCPhotoDB


db=CTCPhotoDB()

f = flickrapi.FlickrAPI(flickr_api_key, flickr_api_secret)




#
#
#	createFlickrSets: Flickr doens not allow creating empty photo sets. So
#	a set can only be created if there's a picture of it already uploaded.
#
#	1. Get all the sets that are not created in Flickr, whose photo no.1 is uploaded
#	2. Created the Flickr sets
#	3. Update their status to created 
#
def getSetsInfoForCreateInFlickr():
	cmd='''
	SELECT sets.set_id, sets.name, photos.hosted_id as photoHid
	FROM photos INNER JOIN sets
	on photos.set_id == sets.set_id
	WHERE photos.order_in_set==0 AND photos.synced & 1 == 1 AND sets.state==0
	'''
	res=db.makeQuery(cmd)
	return res[0]

def createFlickrSet(rec):
	res=f.photosets.create(title=rec["name"],primary_photo_id=rec["photoHid"])
	FlickrSetID=res.find("photoset").attrib["id"]
	db.modifySetByID(rec["set_id"], hosted_id=FlickrSetID, state=1).commit()
	print "Hosted photoset created: ",rec["name"]

def createFlickrSets():
	res=getSetsInfoForCreateInFlickr().fetchall()
	for one in res:
		createFlickrSet(one)




#
#
#	addPhotosToFlickrSets
#
#	1. Find all the photos whose sets are created in Flickr, and themselves uploaded(but not added)
#	2. Add the photos to the Flickr set
#	3. Update the db to keep track of the status
#
def getPhotosInfoForAddingToSetsInFlickr():
	cmd='''
	SELECT photos.photo_id, photos.hosted_id as photoHid, sets.set_id, sets.hosted_id as setHid
	FROM photos INNER JOIN sets
	on photos.set_id == sets.set_id
	WHERE sets.state==1 AND photos.synced & 2 == 0 AND photos.synced & 1 == 1
	'''
	res=db.makeQuery(cmd)
	return res[0]

def addPhotoToFlickrSet(rec):
	#set photos.synced to 2 once added to flickr set
	try:
		f.photosets.addPhoto(photoset_id=rec["setHid"], photo_id=rec["photoHid"])
	except flickrapi.exceptions.FlickrError as e:
		if e.code!=3:	#code 3: already in set. Often because it's the primary photo of the set.
			print e,rec["photoHid"],rec["setHid"]
			return 0
	db.modifyPhotoSynced(rec["photo_id"], 2, rec["set_id"])
	print "added to set: ",rec["photoHid"],rec["setHid"]

def addPhotosToFlickrSets():
	res=getPhotosInfoForAddingToSetsInFlickr().fetchall()
	for one in res:
		addPhotoToFlickrSet(one)




#
#
#	Order the sets in Flickr collection
#
#	1. Get all the sets that are fully uploaded. You can't put orders on pictures that are not uploaded
#	2. For each one of the sets, get their local orders.
#	3. Order the Flickr set with the order 
#
def getAllFullyUploadedSets():
	cmd='''
	SELECT sets.hosted_id, sets.set_id
	FROM photos JOIN sets ON photos.set_id==sets.set_id
	WHERE sets.state==1
	GROUP BY photos.set_id
	HAVING COUNT(case when photos.synced & 2 == 0 then 1 else null end)==0
	--This is a test HAVING COUNT(case when photos.synced & 2 == 2 then 1 else null end)==3
	'''
	res=db.makeQuery(cmd)
	return res[0]

def getOrderedPhotosInSet(set_id):
	cmd='''
	SELECT hosted_id
	FROM photos
	WHERE set_id=='{}' AND synced & 2 ==2
	ORDER BY order_in_set
	'''.format(set_id)
	res=db.makeQuery(cmd)
	return res[0]

def orderFlickrSet(rec):
	photos=getOrderedPhotosInSet(rec["set_id"]).fetchall()
	photoHIDs=",".join([i["hosted_id"] for i in photos])
	f.photosets.reorderPhotos(photoset_id=rec["hosted_id"],photo_ids=photoHIDs)
	db.modifySetByID(rec["set_id"],state=2).commit()
	print "ordered: ",rec["hosted_id"]

def orderFlickrSets():
	res=getAllFullyUploadedSets().fetchall()
	for one in res:
		orderFlickrSet(one)


#
#	
#	Main procedure
#	1. Create the Flickr sets
#	2. Add photos to the sets
#	3. When all photos are added to sets, order them
#
#	All scripts will run the parts of data they can work on. If the data is not workable,
#	It'll stop safely 
#
def CreateAndFillSets():
	createFlickrSets()
	addPhotosToFlickrSets()
	orderFlickrSets()

if __name__=="__main__":
	CreateAndFillSets()