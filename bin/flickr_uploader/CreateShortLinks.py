import sys
import requests
import sqlite3, Queue, threading
import flickrapi
import time, hashlib, math, json

from configs import flickr_api_key, flickr_api_secret, yourls_signature, yourls_URL
from mainDB import CTCPhotoDB

yourlsTimer=0
signature=""

output=""

toShortenList=Queue.Queue()
db_queue=Queue.Queue()


db=CTCPhotoDB()
f = flickrapi.FlickrAPI(flickr_api_key, flickr_api_secret)

boardsTb={
	"uno_gen":["Genuino Uno","ug"],
	"uno_ard":["Arduino Uno","ua"],
	"101_gen":["Genuino 101","101g"],
	"101_ard":["Arduino 101","101a"],
}





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
	url="{yourlsURL}/yourls-api.php?timestamp={timestamp}&signature={signature}&action={action}&format=json"
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



def updateLongURL(shorturl,longurl,title):
	r=yourlsAPI("update",postData={
		"shorturl":shorturl,
		"url":longurl,
		"title":title
	})
	return processYourlsResp(r.text)










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
		if task["taskName"]=="saveShortLink":
			saveShortLink(task)










#
#	Get all photo records from the db who needs 
#	to have its hosted url shortened
#
#
def getUnShortenedPhotos():
	cmd='''
	SELECT photos.photo_id, photos.hosted_url, sets.name
	FROM photos INNER JOIN sets
	ON photos.set_id==sets.set_id
	WHERE photos.synced & 4 != 4 AND photos.hosted_url != ""
	GROUP BY photos.photo_id
	'''
	res=db.makeQuery(cmd)[0].fetchall()
	return res








def makeShortURL(rec,idx,board,set_name):
	#photo_id=rec["photo_id"]
	hosted_url=rec["hosted_url"]
	
	board_name=boardsTb[board][0]
	board_code=boardsTb[board][1]

	keyword="ctc-"
	if set_name.startswith("References"):
		keyword=keyword+"ref-"
	elif set_name.startswith("Concept"):
		keyword=keyword+"con-"

	if set_name.endswith("Noneslideshow"):
		keyword=keyword+"ns-"

	keyword=keyword+"{}-{}-{}"


	title="CTC {} {} {}".format(board_name, set_name, idx)
	keyword=keyword.format(board_code, set_name.split(" ")[1], str(idx))

	return title, keyword

#
#	The whole process of using a record from photos
#	table to get a short url. 
#	
#	There are a few scenarios of return value from 
#	the yourls server. It can return nothing, something
#	not relevant, not "status" field, "status" field 
#	return False, or True.
#
def getShortURL(task):
	res=requestShortURL(task["hosted_url"],task["keyword"],task["title"])

	if res:
		if res["status"]=="success":
			shortURL=res["shorturl"]
			return shortURL
		elif res["code"]=="error:keyword":
			print "Server Message: ", res["message"], ", overwriting"
			res2=updateLongURL(task["keyword"],task["hosted_url"],task["title"])
			if "success" in res2["message"]:
				print "overwritten "+task["keyword"]+" with "+task["hosted_url"]
				return task["keyword"]
			else:
				print "Failed to overwrite "+photo_id
				raise
			'''
			print res["message"], "attemp recovering"
			res2=expandShortURL(keyword)
			if res2["message"]=="success":
				if res2["longurl"]==hosted_url:
					print "Recovered"+res2["shorturl"]
					return res2["shorturl"]
			else:
				print "Failed to recover "+photo_id
			'''
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














def getFullyUploadedSets(toDoOnly=True):
	cmd='''
	SELECT sets.set_id, sets.name
	FROM photos JOIN sets ON photos.set_id==sets.set_id
	{}
	GROUP BY photos.set_id
	HAVING COUNT(case when photos.synced & 2 == 0 then 1 else null end)==0
	'''
	if toDoOnly:
		where="WHERE sets.shortlinked == 0"
	else:
		where=""
	res=db.makeQuery(cmd.format(where))[0].fetchall()
	return res

def getVersionedPhotosBySet(rec):
	cmd='''
	SELECT photos.photo_id, photos.hosted_url, photos.photo_id, photos.file_name
	FROM photos INNER JOIN sets
	ON photos.set_id==sets.set_id
	WHERE sets.set_id=="{}" AND (photos.board_version == "" OR photos.board_version LIKE "%{}%")
	GROUP BY photos.photo_id
	ORDER BY photos.order_in_set
	'''
	resAll={}
	for board in boardsTb:
		res=db.makeQuery(cmd.format(rec["set_id"],board))[0].fetchall()
		resAll[board]=res
	return resAll

def makeShortLinkForBoard(photos,board,photoSet):
	#global output
	for i,photo in enumerate(photos):
		title,keyword=makeShortURL(photo,i,board,photoSet["name"])
		#print title,keyword, photo["photo_id"]
		#output=output+"<photo>\n<filename>{}</filename>\n<shortlink>http://verkstad.cc/urler/{}</shortlink>\n</photo>\n".format(photo["file_name"],keyword)
		toShortenList.put({"title":title, "keyword":keyword, "photo_id":photo["photo_id"], "hosted_url":photo["hosted_url"]})









def outputShortLinks():
	global output
	targetSets=getFullyUploadedSets(False)

	output=output+"<data>\n"
	for photoSet in targetSets:
		output=output+"<photoSet name='{}'>\n".format(photoSet["name"])

		versionedPhotos=getVersionedPhotosBySet(photoSet)
		for board,photos in versionedPhotos.iteritems():
			output=output+"<board type='{}'>\n".format(boardsTb[board][0])
			for i,photo in enumerate(photos):
				title,keyword=makeShortURL(photo,i,board,photoSet["name"])
				output=output+"<photo>\n<filename>{}</filename>\n<shortlink>http://verkstad.cc/urler/{}</shortlink>\n</photo>\n".format(photo["file_name"],keyword)
			output=output+"</board>\n"

		output=output+"</photoSet>\n"
	output=output+"</data>\n"


def createShortLinks():
	#global output
	targetSets=getFullyUploadedSets()

	print "Photo sets needs to be processed:"

	for one in targetSets:
		print one["name"]

	createWorkers(5,urlShortenTask, toShortenList)

	print "Start generating short links"

	for photoSet in targetSets:
		print photoSet["name"],"############################################"

		versionedPhotos=getVersionedPhotosBySet(photoSet)
		for board,photos in versionedPhotos.iteritems():
			print board, "-----------------------"
			makeShortLinkForBoard(photos,board,photoSet)

			while toShortenList.qsize()>0:
				mainDBWork()
			mainDBWork()

		db.modifySetByID(photoSet["set_id"],shortlinked=1).commit()


def createAndOutputShortLinks():
	print "Creating short links"
	createShortLinks()

	print "Output short links to testRes.txt"
	outputShortLinks()
	
	f=open("testRes.txt","w")
	f.write(output)
	f.close()



if __name__=="__main__":
	'''
	if "--create" in sys.argv:
		print "creating short links"
		createShortLinks()
	else:
		print "output shortlinks only"	
	
	print "output shortlinks to testRes.txt"
	outputShortLinks()
	'''

	'''
	rec=db.getPhotoByID("863288")
	print makeShortURL(rec,0,"uno_gen","Block 01-01 Red Snake Noneslideshow")
	rec=db.getPhotoByID("863288")
	print makeShortURL(rec,0,"uno_gen","Block 01-01 Red Snake noneslideshow")
	rec=db.getPhotoByID("723217")
	print makeShortURL(rec,2,"uno_gen","Block 03-06 POV")
	rec=db.getPhotoByID("864643")
	print makeShortURL(rec,2,"uno_gen","Concept 04-02 Types Of Motors Noneslideshow")
	rec=db.getPhotoByID("865699")
	print makeShortURL(rec,1,"101_gen","References 29 Potentiometer Noneslideshow")
	'''
	
	#updateLongURL("ctc-ua-02-07-1","google.com","google.com")
	#expandShortURL("ctc-ua-02-07-15")