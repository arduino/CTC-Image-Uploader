import flickrapi
import threading, Queue
import time, os

from configs import flickr_api_key, flickr_api_secret
from mainDB import CTCPhotoDB

from CreateAndFillSets import CreateAndFillSets
from fetchURLAndGenShortLink import fetchURLAndGenShortLink


f = flickrapi.FlickrAPI(flickr_api_key, flickr_api_secret)

upload_queue=Queue.Queue()
upload_workers=[]

db_queue=Queue.Queue()

db=CTCPhotoDB()



#
#
#	Utility for getting path to a file based on db record.
#	It checks if the file exists
#
#
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

def getFilenameFromRec(rec,db=db):
	baseName=rec["file_name"]
	if rec["folder"]:
		field="folder"
	else:
		field="set_id"
	setName=db.getSetByID(rec[field])["name"]
	filename=""
	try:
		filename=getFilename(baseName,setName)
	except Exception as e:
		pass #Ignoring non-exisiting files, since most files don't exist 
		#print e
	return filename


#
#	Specify folder location for linked pictures
#	If a picture is used in more than one sets, set the file location
#	to the one that's existing.
#
#
# "folder" field is used for photo records reusing the same file location
# When mutiple photos are linking to the same folder, the folder value
# will be replaced by the set_id of the one physically exisits. 
#
# i.e. if there are 2 records of the same image in different sets:  
#       photo_id    file_name   set_id  folder
#       740853      P5620073    683635  
#       740853      P5620073    683605  
# 
#	if when uploading files, it is found out that the first has a file associated
# both of their folder will be replaced with 683635
#
def saveSetIDToFolder(rec):
	cmd="""
	UPDATE photos
	SET folder={}
	WHERE photo_id=={}
	""".format(rec["set_id"],rec["photo_id"])
	db.makeQuery(cmd)[1].commit()


#
#
#	Worker threads for uploading a picture.
#	1. Find out the file of the picture to be uploaded
#	2. Upload the file, and give the Flickr ID to the main thread for saving
#
def uploadPhoto(index, queue):
	while True:
		task=queue.get()
		filename=task["filename"]
		rec=task["rec"]
		print "worker {} uploading {}".format(index,filename)
		res=f.upload(filename,title=rec["file_name"])
		photoid=res.find("photoid").text
		print photoid
		db_queue.put({"taskName":"saveFlickrID","rec":rec,"photoid":photoid})
		#print photoid
		#time.sleep(2)
		queue.task_done()

def createUploadWorkers(num):
	for i in range(num):
		worker=threading.Thread(target=uploadPhoto, args=(i,upload_queue))
		worker.setDaemon(True)
		upload_workers.append(worker)
		worker.start()



#
#
#	In main thread, save the status and flickr ID of photos that has been uploaded
#
#
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
		if task["taskName"]=="saveFlickrID":
			photoid=task["photoid"]
			print "recording {}".format(photoid)
			saveFlickrID(rec,photoid)
		elif task["taskName"]=="saveSetIDToFolder":
			saveSetIDToFolder(rec)

#
#	
#	Upload all pictures to flickr
#	1. Create worker threads for uploading
#	2. Get all records of photos that need to be uploaded
#	3. Specify the folder location if not set
#	4. Don't upload if the file is already uploaded, or file does not exist
#	5. Wait if the upload queue is too long
#	6. Add task to upload queue
#	7. Save the status of uploaded pictures to db
#
def uploadPictures():
	createUploadWorkers(5)
	#createDBWorker()

	pics=db.getAllPhotos()
	print len(pics), "pictures in total"
	for one in pics:
		if one["synced"]:
			continue

		filename=getFilenameFromRec(one)
		if filename=="":
			continue
		
		if one["folder"]=="":
			db_queue.put({"taskName":"saveSetIDToFolder","rec":one})

		#wait while upload_queue is processed
		while True:
			main_dbWork(db_queue)
			if upload_queue.qsize()<100:
				break

		print filename, "will be uploaded"
		upload_queue.put({"filename":filename,"rec":one})

	upload_queue.join()
	main_dbWork(db_queue)



if __name__=="__main__":
	f.authenticate_via_browser(perms='delete')

	uploadPictures()
	print("all pictures Uploaded")

	CreateAndFillSets()
	print("All Sets created and filled")

	fetchURLAndGenShortLink()
	print("All hosted URLs saved, short links created")

