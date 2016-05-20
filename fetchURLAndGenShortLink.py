import sqlite3, Queue, threading
import flickrapi
import time

from configs import flickr_api_key, flickr_api_secret, yourls_signature
from mainDB import CTCPhotoDB


photos_list=Queue.Queue()
photo_urls=Queue.Queue()


db=CTCPhotoDB()

f = flickrapi.FlickrAPI(flickr_api_key, flickr_api_secret)

#
#	Get all photos which should have their flickr url updated
#
#
def getPhotosHIDForFlickr():
	cmd='''
	SELECT *
	FROM photos 
	WHERE hosted_url == "" AND synced & 1 == 1
	'''
	return db.makeQuery(cmd)[0].fetchall()



#
#	Retrive info about picture from Flickr, and assemble the photo urls
#	PNG and JPG use different rules for assembling photo urls
#
# See: 
# api for getting photo urls directly: https://www.flickr.com/services/api/flickr.photos.getSizes.html
# api for getting photo info: https://www.flickr.com/services/api/flickr.photos.getInfo.html
#
def getFlickrURL(rec):
	info=f.photos.getInfo(photo_id=rec["hosted_id"])
	base=info.find("photo")
	format=base.attrib["originalformat"]
	if format=="png":
		url="https://farm{farm}.staticflickr.com/{server}/{id}_{originalsecret}_o.{originalformat}".format(**base.attrib)
	elif format=="jpg":
		url="https://farm{farm}.staticflickr.com/{server}/{id}_{secret}_z.{originalformat}".format(**base.attrib)

	photo_urls.put({"photo_id":rec["photo_id"],"hosted_url":url})

#
#	Save a Flcikr URL to the database
#
#
def saveFlickrURL(data):
	db.modifyPhotoByID(data["photo_id"],hosted_url="'{}'".format(data["hosted_url"]))
	db.commit()
	print data["photo_id"]," saved"

#
#	Worker task of handling Flickr URLs
#
#
def flickrURLTask(index,queue):
	while True:
		task=queue.get()
		res=getFlickrURL(task)
		queue.task_done()




#
#	Create webworkers for handling tasks
#
#
def createWorkers(num,target,queue):
	for i in range(num):
		worker=threading.Thread(target=target,args=(i, queue))
		worker.setDaemon(True)
		worker.start()

#
#	main thread worker, saves data into db.
#	It should save: Flickr URL and shorterned URL
#
#	TO-DO: Save shorterned URL
#
def mainDBWork():
	while True:
		try:
			task=photo_urls.get(False)
		except Queue.Empty:
			break
		#print task["photo_id"], task["hosted_url"]
		saveFlickrURL(task)



def connectToShortener():
	ct=int(time.time())
	#sign=


def getShortURL():
	pass


#
#	Steps for generating the urls and saving them
#
#	1. Get all records where urls need to be updated
# 2. Create web workers to fetch urls from flickr
# 3. Create web workers to generate short urls
# 4. In main thread, save the urls to db 
#
#	TO-DO: Add short urls into workflow
#
def fetchURLAndGenShortLink():
	for one in getPhotosHIDForFlickr():
		#print one
		photos_list.put(one)

	createWorkers(5,flickrURLTask, photos_list)

	while photos_list.qsize()>0:
		mainDBWork()
	photos_list.join()
	mainDBWork()

if __name__=="__main__":
	fetchURLAndGenShortLink()