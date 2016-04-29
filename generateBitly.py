import sqlite3, Queue, threading
import flickrapi
from mainDB import CTCPhotoDB


photos_list=Queue.Queue()
photo_urls=Queue.Queue()

flickr_api_key = u'c1b9a319a2e25dbcd49ca1eea44a5990'
flickr_api_secret = u'f4b371ff599357ed'

db=CTCPhotoDB()

f = flickrapi.FlickrAPI(flickr_api_key, flickr_api_secret)

def getPhotosHIDForFlickr():
	cmd='''
	SELECT *
	FROM photos 
	WHERE hosted_url == "" AND synced & 1 == 1
	'''
	return db.makeQuery(cmd)[0].fetchall()

def getFlickrURL(rec):
	info=f.photos.getInfo(photo_id=rec["hosted_id"])
	#https://farm" + farm + ".staticflickr.com/" + server + "/" + id + "_" + secret + "_z.jpg
	base=info.find("photo")
	url="https://farm{farm}.staticflickr.com/{server}/{id}_{secret}_z.{originalformat}".format(**base.attrib)

	photo_urls.put({"photo_id":rec["photo_id"],"hosted_url":url})


def saveFlickrURL(data):
	db.modifyPhotoByID(data["photo_id"],hosted_url="'{}'".format(data["hosted_url"]))
	db.commit()
	print data["photo_id"]," saved"


def mainDBWork():
	while True:
		try:
			task=photo_urls.get(False)
		except Queue.Empty:
			break
		#print task["photo_id"], task["hosted_url"]
		saveFlickrURL(task)

def flickrURLTask(index,queue):
	while True:
		task=queue.get()
		res=getFlickrURL(task)
		queue.task_done()

def createWorkers(num,target,queue):
	for i in range(num):
		worker=threading.Thread(target=target,args=(i, queue))
		worker.setDaemon(True)
		worker.start()

def procedure():
	for one in getPhotosHIDForFlickr():
		print one
		photos_list.put(one)

	createWorkers(5,flickrURLTask, photos_list)

	while photos_list.qsize()>0:
		mainDBWork()
	photos_list.join()
	mainDBWork()

if __name__=="__main__":
	procedure()