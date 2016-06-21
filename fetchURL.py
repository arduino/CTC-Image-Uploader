import requests
import sqlite3, Queue, threading
import flickrapi
import time, hashlib, math, json

from configs import flickr_api_key, flickr_api_secret, yourls_signature, yourls_URL
from mainDB import CTCPhotoDB

yourlsTimer=0
signature=""

photos_list=Queue.Queue()
db_queue=Queue.Queue()
unshortened_list=Queue.Queue()


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

	db_queue.put({"taskName":"saveHostedURL","photo_id":rec["photo_id"],"hosted_url":url})

#
#	Save a Flcikr URL to the database
#
#
def saveFlickrURL(data):
	db.setPhotoHostedURL(data["photo_id"],hosted_url=data["hosted_url"])
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
#	It saves: Flickr URL and shorterned URL
#
#
def mainDBWork():
	while True:
		try:
			task=db_queue.get(False)
		except Queue.Empty:
			break
		#print task["photo_id"], task["hosted_url"]
		if task["taskName"]=="saveHostedURL":
			saveFlickrURL(task)










#
#	Steps for generating the urls and saving them
#
# 1. Get all records where urls need to be updated
# 2. Create web workers to fetch urls from flickr
# 3. Wait for done, save to db meanwhile
#
#


# 4. Get all photoSets with full photos
# 5. Retrive the photos in the right order, based on boards
# 6. 
# 3. Get all records where short url needs to be generated
# 4. Create web workers to generate short urls
# 5. Wait for the urls to be fetched from flickr
# 6. Wait for the short urls to be generated
# 7. In main thread, save the urls to db 
#
#
def fetchURL():
	for one in getPhotosHIDForFlickr():
		#print one
		photos_list.put(one)

	createWorkers(5,flickrURLTask, photos_list)

	while photos_list.qsize()>0:
		mainDBWork()
	photos_list.join()

	mainDBWork()

	'''
	for one in getUnShortenedPhotos():
		unshortened_list.put(one)

	createWorkers(5,urlShortenTask, unshortened_list)

	while unshortened_list.qsize()>0:
		mainDBWork()
	unshortened_list.join()

	mainDBWork()
	'''


if __name__=="__main__":

	fetchURL()
	'''
	for i in range(1):
		print requestShortURL("http://google.com","goog{}".format(1),"goog{}".format(i))
		time.sleep(3)
	'''
	#print json.loads(expandShortURL("goog1"))["longurl"]=="http://google.com"