import flickrapi
import threading, Queue
import time, os

from mainDB import CTCPhotoDB

flickr_api_key = u'c1b9a319a2e25dbcd49ca1eea44a5990'
flickr_api_secret = u'f4b371ff599357ed'

f = flickrapi.FlickrAPI(flickr_api_key, flickr_api_secret)

upload_queue=Queue.Queue()
upload_workers=[]

db_queue=Queue.Queue()

db=CTCPhotoDB()




def getFilename(baseName,setName):
	filename_woExt="./data/images/"+setName.replace(" ","_")+"/"+baseName
	filename=""
	if os.path.exists(filename_woExt+".jpg"):
		filename=filename_woExt+".jpg"
	elif os.path.exists(filename_woExt+".png"):
		filename=filename_woExt+".png"
	else:
		#print filename_woExt+" does not exist"
		raise Exception(filename_woExt+" does not exist")
	return filename

def getFilenameFromRec(rec):
	baseName=rec["file_name"]
	setName=db.getSetByID(rec['set_id'])["name"]
	filename=""
	try:
		filename=getFilename(baseName,setName)
	except Exception as e:
		pass
		#print e
	return filename





def uploadPhoto(index, queue):
	while True:
		task=queue.get()
		filename=task["filename"]
		rec=task["rec"]
		print "worker {} uploading {}".format(index,filename)
		res=f.upload(filename,title=rec["file_name"])
		photoid=res.find("photoid").text
		print photoid
		db_queue.put({"rec":rec,"photoid":photoid})
		#print photoid
		#time.sleep(2)
		queue.task_done()

def createUploadWorkers(num):
	for i in range(num):
		worker=threading.Thread(target=uploadPhoto, args=(i,upload_queue))
		worker.setDaemon(True)
		upload_workers.append(worker)
		worker.start()




def saveFlickrID(rec,flickr_id):
	print rec["photo_id"],flickr_id
	db.setPhotoHostedID(rec["photo_id"],flickr_id)

def main_dbWork(queue):
	while True:
		try:
			#print queue.qsize()
			task=queue.get(False)
		except Queue.Empty:
			break
		rec=task["rec"]
		photoid=task["photoid"]
		print "recording {}".format(photoid)
		saveFlickrID(rec,photoid)




def uploadPictures():
	createUploadWorkers(5)
	#createDBWorker()

	pics=db.getAllPhotos()
	#pics=db.getPhotosBySetID(683635)
	for one in pics:
		if one["synced"]:
			continue

		filename=getFilenameFromRec(one)
		if filename=="":
			continue
		
		#wait while upload_queue is processed
		while True:
			main_dbWork(db_queue)
			if upload_queue.qsize()<100:
				break
		upload_queue.put({"filename":filename,"rec":one})

	upload_queue.join()
	main_dbWork(db_queue)



if __name__=="__main__":
	f.authenticate_via_browser(perms='delete')

	#createPhotoSets()
	uploadPictures()
	#saveFlickrID({"ID":"684889"},"wttf")
	#res=f.photos.getInfo(photo_id="16754246842")
	#for one in res.find("photo"):
	#	print one
	#print res.find("photo").find("title").text
	#f.photos.delete(photo_id=res.find("photoid").text)

