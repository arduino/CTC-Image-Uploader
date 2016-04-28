import sqlite3
import flickrapi

from mainDB import CTCPhotoDB

flickr_api_key = u'c1b9a319a2e25dbcd49ca1eea44a5990'
flickr_api_secret = u'f4b371ff599357ed'

db=CTCPhotoDB()

f = flickrapi.FlickrAPI(flickr_api_key, flickr_api_secret)
#
#
#	createFlickrSets
#
#
def getSetsInfoForCreateInFlickr():
	cmd='''
	SELECT sets.set_id, sets.name, photos.hosted_id as photoHid
	FROM photos INNER JOIN sets
	on photos.set_id == sets.set_id
	WHERE photos.order_in_set==0 AND photos.synced==1 AND sets.state==0
	'''
	res=db.makeQuery(cmd)
	return res[0]

def createFlickrSet(rec):
	res=f.photosets.create(title=rec["name"],primary_photo_id=rec["photoHid"])
	FlickrSetID=res.attrib["id"]
	db.modifySetByID(rec["set_id"], hosted_id=FlickrSetID, state=1)

def createFlickrSets():
	res=getSetsInfoForCreateInFlickr().fetchall()
	for one in res:
		createFlickrSet(one)




#
#
#	addPhotosToFlickrSets
#
#
def getPhotosInfoForAddingToSetsInFlickr():
	cmd='''
	SELECT photos.photo_id, photos.hosted_id as photoHid, sets.set_id, sets.hosted_id as setHid
	FROM photos INNER JOIN sets
	on photos.set_id == sets.set_id
	WHERE sets.state==1 AND photos.synced==1
	'''
	res=db.makeQuery(cmd)
	return res[0]

def addPhotoToFlickrSet(rec):
	#set photos.synced to 2 once added to flickr set
	try:
		f.photosets.addPhoto(photoset_id=rec["setHid"], photo_id=rec["photoHid"])
		db.modifyPhotoSynced(rec["photo_id"], 2, rec["set_id"])
		print "added: ",rec["photoHid"],rec["setHid"]
	except flickrapi.exceptions.FlickrError as e:
		print e,rec["photoHid"],rec["setHid"]


def addPhotosToFlickrSets():
	res=getPhotosInfoForAddingToSetsInFlickr().fetchall()
	for one in res:
		addPhotoToFlickrSet(one)




#
#
#
#
#
def getAllFullyUploadedSets():
	cmd='''
	SELECT photos.set_id
	FROM photos JOIN sets ON photos.set_id==sets.set_id
	WHERE sets.state==1
	GROUP BY photos.set_id
	--HAVING COUNT(case when photos.synced<2 then 1 else null end)==0
	HAVING COUNT(case when photos.synced>0 then 1 else null end)!=0
	'''
	res=db.makeQuery(cmd)
	return res[0]

def getOrderedPhotosInSet(set_id):
	cmd='''
	SELECT hosted_id
	FROM photos
	WHERE set_id=='{}'
	ORDER BY order_in_set
	'''.format(set_id)
	res=db.makeQuery(cmd)
	return res[0]

def orderFlickrSet(rec):
	photos=getOrderedPhotosInSet(rec["set_id"]).fetchall()
	photoIDs=[i[0] for i in photos]
	print rec["set_id"], photoIDs, len(photoIDs)
	#f.photoset.reorderPhotos(photoset_id=rec["set_id"],photo_ids=photoIDs)
	#db.modifySetByID(rec["set_id"],state=1)
	#db.commit()

def orderFlickrSets():
	res=getAllFullyUploadedSets().fetchall()
	for one in res:
		orderFlickrSet(one)

if __name__=="__main__":
	#createFlickrSets()
	addPhotosToFlickrSets()
	#orderFlickrSets()