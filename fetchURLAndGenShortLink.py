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
		elif task["taskName"]=="saveShortLink":
			saveShortLink(task)



#
#	Get all photo records from the db who needs 
#	to have its hosted url shortened
#
#
def getUnShortenedPhotos():
	cmd='''
	SELECT photos.photo_id, photos.hosted_url, photos.order_in_set, sets.name
	FROM photos INNER JOIN sets
	ON photos.set_id==sets.set_id
	WHERE photos.synced & 4 != 4 AND photos.hosted_url != ""
	GROUP BY photos.photo_id	
	'''
	return db.makeQuery(cmd)[0].fetchall()










#
#	Get an authentication token for yourls, by
# either generating it with the time or getting
# an unexpired one
#
def getYourlsToken():
	global yourlsTimer, signature
	currentTime=time.time()
	if currentTime-yourlsTimer>3600:
		yourlsTimer=currentTime
		m=hashlib.md5()
		m.update(str(int(yourlsTimer))+yourls_signature)
		signature=m.hexdigest()

	return signature, str(int(yourlsTimer))

#
#	Making a API call to yourls server.
#
#
def yourlsAPI(action, postData):
	url="{yourlsURL}/yourls-api.php?timestamp={timestamp}&signature={signature}&action={action}"
	signature, timestamp=getYourlsToken()
	yourlsURL=yourls_URL
	url=url.format(**locals())

	r=requests.post(url,data=postData)
	return r

#
#	Handling response from the yourls server, dealing
#	with different errors
#
def processYourlsResp(resp):
	try:
		res=json.loads(resp)
	except ValueError:
		print "Server didn't return json response"
	except:
		#Any other exceptions
		raise
	else:
		if "statusCode" in res:
			return res
		else:
			#Coudln't get to the shortener service
			print "Server error", res
	return False

#
#	Request short url from yourls by providing the 
# long url, requiring short url and the identifying
# title
#
def requestShortURL(longURL,keyword,title):
	r=yourlsAPI("shorturl",postData={
		"url":longURL,
		"keyword":keyword,
		"title":title,
		"format":"json",
	})
	return processYourlsResp(r.text)

#
#	Request short url from yourls by providing the 
# keyword, looking up an existing short url for
#	the long url
#
def expandShortURL(shorturl):
	r=yourlsAPI("expand",postData={
		"shorturl":shorturl,
		"format":"json",
	})
	return processYourlsResp(r.text)










#
#	The whole process of using a record from photos
#	table to get a short url. 
#	
#	There are a few scenarios of return value from 
#	the yourls server. It can return nothing, something
#	not relevant, not "status" field, "status" field 
#	return False, or True.
#
def getShortURL(rec):
	photo_id=rec["photo_id"]
	hosted_url=rec["hosted_url"]
	set_name=rec["name"]
	order_in_set=rec["order_in_set"]

	title="CTC {} slideshow {}".format(set_name, order_in_set)
	keyword="ctc-s-"+set_name.split(" ")[1]+"-"+str(order_in_set)
	#print keyword
	res=requestShortURL(hosted_url,keyword,title)

	if res:
		if res["status"]=="success":
			shortURL=res["shorturl"]
			return shortURL
		elif res["code"]=="error:keyword":
			print res["message"], "attemp recovering"
			res2=expandShortURL(keyword)
			if res2["message"]=="success":
				if res2["longurl"]==hosted_url:
					print "Recovered"+res2["shorturl"]
					return res2["shorturl"]
			else:
				print "Failed to recover "+photo_id
	else:
		return res


#
#	The whole process of using a record from
#	photos table to get a short url. 
#
def urlShortenTask(index,queue):
	while True:
		task=queue.get()
		res=getShortURL(task)
		if res:
			toSave={"taskName":"saveShortLink","photo_id":task["photo_id"],"refering_url":res}
			db_queue.put(toSave)
		queue.task_done()

#
#	Actual DB work to save the short link
#
def saveShortLink(task):
	db.setPhotoReferingURL(task["photo_id"],task["refering_url"])
	print task["photo_id"]," shortened"








#
#	Steps for generating the urls and saving them
#
#	1. Get all records where urls need to be updated
# 2. Create web workers to fetch urls from flickr
#	3. Get all records where short url needs to be generated
# 4. Create web workers to generate short urls
# 5. Wait for the urls to be fetched from flickr
# 6. Wait for the short urls to be generated
# 7. In main thread, save the urls to db 
#
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
		print requestShortURL("http://google.com","goog{}".format(1),"goog{}".format(i))
		time.sleep(3)
	'''
	#print json.loads(expandShortURL("goog1"))["longurl"]=="http://google.com"