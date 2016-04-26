import flickrapi
import threading, Queue
import time, os

from mainDB import CTCPhotoDB

flickr_api_key = u'c1b9a319a2e25dbcd49ca1eea44a5990'
flickr_api_secret = u'f4b371ff599357ed'

upload_queue=Queue.Queue()
upload_workers=[]
db=CTCPhotoDB()

'''
def main():
	uploadPictures()
	createPhotoSets()
	addPicsToSets()
	orderPics()
'''

def saveFlickrID(rec,flickr_id):
	db.setPhotoHostedID(rec["ID"],flickr_id)

def createPhotoSet(set_id,setName):
	#res=f.photosets.create(title=setName)
	#db.modifySetByID(id=set_id, hosted_url=res.attrib["id"])
	db.modifySetByID(set_id=set_id, hosted_url="bla")

def createPhotoSets():
	#create photosets in flickr
	photoSets=db.getAllSets()
	print photoSets
	for one in photoSets:
		#print type(one)
		createPhotoSet(one["set_id"],one["name"])
	#db.commit()


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

def uploadPictures():
	createWorkers(5)

	pics=db.getAllPhotos()
	#pics=db.getPhotosBySetID(683635)
	for one in pics:
		if one["synced"]:
			continue

		filename=getFilenameFromRec(one)
		if filename=="":
			continue
		
		#print filename

		#wait while upload_queue is processed
		while upload_queue.qsize()>100:
			pass
		upload_queue.put({"filename":filename,"rec":one})

	upload_queue.join()

def createWorkers(num):
	for i in range(num):
		worker=threading.Thread(target=uploadPhoto, args=(i,upload_queue))
		worker.setDaemon(True)
		upload_workers.append(worker)
		worker.start()

def uploadPhoto(index, queue):
	global f
	#res=f.upload(filename="data/images/block_2-3_fencing/block_2-3_fencing_step-1.png")
	#print res.find("photoid").text
	while True:
		task=queue.get()
		filename=task["filename"]
		rec=task["rec"]
		print "worker {} uploading {}".format(index,filename)
		res=f.upload(filename,title=rec["file_name"])
		photoid=res.find("photoid").text
		print photoid
		#saveFlickrID(rec,photoid)
		#time.sleep(2)
		#f.photos.delete(photo_id=photoid)
		queue.task_done()



if __name__=="__main__":
	global f
	f = flickrapi.FlickrAPI(flickr_api_key, flickr_api_secret)
	f.authenticate_via_browser(perms='delete')

	#createPhotoSets()
	uploadPictures()
	#saveFlickrID({"ID":"684889"},"wttf")
	#res=f.photos.getInfo(photo_id="16754246842")
	#for one in res.find("photo"):
	#	print one
	#print res.find("photo").find("title").text
	#f.photos.delete(photo_id=res.find("photoid").text)

