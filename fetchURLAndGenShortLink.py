import requests
import sqlite3, Queue, threading
import flickrapi
import time, hashlib, math, json

from configs import flickr_api_key, flickr_api_secret, yourls_signature, yourls_URL
from mainDB import CTCPhotoDB

yourlsTimer=0
signature=""

photos_list=Queue.Queue()
hosted_urls=Queue.Queue()
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

	hosted_urls.put({"photo_id":rec["photo_id"],"hosted_url":url})

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
			task=hosted_urls.get(False)
		except Queue.Empty:
			break
		#print task["photo_id"], task["hosted_url"]
		saveFlickrURL(task)




def getUnShortenedPhotos():
	cmd='''
	SELECT photos.photo_id, photos.hosted_url, photos.order_in_set, sets.name
	FROM photos INNER JOIN sets
	ON photos.set_id==sets.set_id
	WHERE photos.synced & 4 != 4 AND photos.hosted_url != ""
	GROUP BY photos.photo_id	
	'''
	return db.makeQuery(cmd)[0].fetchall()

def getYourlsToken():
	global yourlsTimer, signature
	currentTime=time.time()
	if currentTime-yourlsTimer>3600:
		yourlsTimer=currentTime
		m=hashlib.md5()
		m.update(str(int(yourlsTimer))+yourls_signature)
		signature=m.hexdigest()

	return signature, str(int(yourlsTimer))

def requestShortURL(longURL,keyword,title):
	#global yourlsURL
	url="{yourlsURL}/yourls-api.php?timestamp={timestamp}&signature={signature}&action={action}"
	signature, timestamp=getYourlsToken()
	action="shorturl"
	yourlsURL=yourls_URL
	url=url.format(**locals())
	#print url

	r=requests.post(url,data={
		"url":longURL,
		"keyword":keyword,
		"title":title,
		"format":"json",
	})
	return r.text


def getShortURL(rec):
	photo_id=rec["photo_id"]
	hosted_url=rec["hosted_url"]
	set_name=rec["name"]
	order_in_set=rec["order_in_set"]

	title="CTC {} slideshow {}".format(set_name, order_in_set)
	keyword="ctc-s-"+set_name.split(" ")[1]+"-"+str(order_in_set)
	#print keyword
	res=requestShortURL(hosted_url,keyword,title)

	try:
		res=json.loads(res)
	except ValueError:
		print "Server didn't return json response"
	except:
		raise
	else:
		if("status" in res):
			if(res["status"]=="success"):
				shortURL=res["shorturl"]
				toSave={"photo_id":photo_id,"refering_url":shortURL}
				print toSave
			else:
				print res["message"]
		else:
			print "Server error", res


def urlShortenTask(index,queue):
	while True:
		task=queue.get()
		res=getShortURL(task)
		queue.task_done()


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


	for one in getUnShortenedPhotos()[0:1]:
		unshortened_list.put(one)

	createWorkers(5,urlShortenTask, unshortened_list)


	while photos_list.qsize()>0:
		mainDBWork()
	photos_list.join()


	while unshortened_list.qsize()>0:
		mainDBWork()
	unshortened_list.join()


	mainDBWork()

if __name__=="__main__":
	fetchURLAndGenShortLink()
	'''
	for i in range(1):
		requestShortURL("http://google.com","goog{}".format(i),"goog{}".format(i))
		time.sleep(3)
	'''