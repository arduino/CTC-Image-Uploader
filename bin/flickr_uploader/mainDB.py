import sqlite3, datetime, os

class CTCPhotoDB:
	def __init__(self, db_file="maindb.db"):
		self.conn=sqlite3.connect(db_file)
		self.conn.row_factory = sqlite3.Row

	def commit(self):
		self.conn.commit()
	
	def close(self):
		self.conn.close()





	#
	#	Create Tables, for first time use
	#
	#
	def createTables(self):
		cmds=['''
		CREATE TABLE IF NOT EXISTS photos(
			ID PRIMARY KEY,
			photo_id CHAR(15),
			file_name CHAR(50),
			set_id INT,
			folder INT,
			order_in_set INT,
			board_version CHAR(125),
			hosted_url CHAR(255),
			hosted_id CHAR(15),
			refering_url CHAR(125),
			last_updated DATETIME,
			synced TINYINT DEFAULT 0
		);
		''',
		'''
		CREATE TABLE IF NOT EXISTS sets(
			set_id PRIMARY KEY,
			name CHAR(125),
			hosted_id CHAR(15),
			state TINYINT,
			shortlinked TinyInt
		);
		''',
		'''
		CREATE TABLE IF NOT EXISTS extras(
			name CHAR(125),
			type CHAR(15),
			short_code CHAR(30) PRIMARY KEY,
			hosted_url CHAR(255),
			set_id INT,
			order_in_set INT,
			state TINYINT
		);
		''']

		for cmd in cmds:
			self.makeQuery(cmd)





	#
	#	Add a record to sets table.
	#	values must be packed into a dictionary.
	#
	#
	def addSet(self, pack):
		ipt=updatedInput({"set_id":"","name":"","hosted_id":"","state":0,"shortlinked":0},pack)
		cmd='''
		INSERT OR IGNORE INTO sets VALUES
		('{set_id}','{name}','{hosted_id}','{state}','{shortlinked}')
		'''.format(**ipt)

		self.makeQuery(cmd)

	#
	#	Add a record to photos table.
	#	values must be packed into a dictionary.
	#
	#
	def addPhoto(self,pack):
		basePack={
			"ID":"",
			"photo_id":"",
			"file_name":"",
			"set_id":"",
			"folder":"",
			"order_in_set":-1,
			"board_version":"",
			"hosted_url":"",
			"hosted_id":"",
			"refering_url":"",
			"last_updated":datetime.datetime.now(),
			"synced":0
		}
		ipt=updatedInput(basePack,pack)
		cmd='''
		INSERT OR IGNORE INTO photos VALUES
		('{ID}','{photo_id}','{file_name}','{set_id}','{folder}',{order_in_set},'{board_version}','{hosted_url}','{hosted_id}','{refering_url}','{last_updated}',{synced})
		'''.format(**ipt)

		self.makeQuery(cmd)

	#
	#	Add a record to extras table.
	#	values must be packed into a dictionary.
	#
	#
	def addExtra(self,pack):
		basePack={
			"name":"",
			"type":"",
			"short_code":"",
			"hosted_url":"",
			"set_id":"",
			"order_in_set":0,
			"state":0
		}
		ipt=updatedInput(basePack,pack)
		cmd='''
		INSERT OR IGNORE INTO extras VALUES
		('{name}','{type}','{short_code}','{hosted_url}','{set_id}',{order_in_set},'{state}')
		'''.format(**ipt)

		self.makeQuery(cmd)






	#
	#	Modify the state of a set record
	#
	#
	def modifySetState(self,set_id,state):
		self.modifySetByID(set_id,state=state).commit()

	#
	#	Modify a set by values set in kwargs
	#
	#
	def modifySetByID(self, set_id, **kwargs):
		set_id="'{}'".format(set_id)
		return self.modifyRec("sets",{"set_id":set_id}, kwargs)

	#
	#	Remove hosted information about a photo set
	#
	#
	def cleanSetByID(self, set_id):
		return self.modifySetByID(set_id, state=0, hosted_id="''")



	#
	#	Set the hosted_id of a photo.
	#	It is assumed that the photo is uploaded. Thus the first bit of synced is set 1
	#
	def setPhotoHostedID(self, photo_id, hosted_id):
		hosted_id="'{}'".format(hosted_id)
		self.modifyPhotoByID_UpdateSynced(photo_id,hosted_id=hosted_id,synced=1).commit()

	#
	#	Set the hosted_url of a photo.
	#
	#
	def setPhotoHostedURL(self, photo_id, hosted_url):
		hosted_url="'{}'".format(hosted_url)
		self.modifyPhotoByID(photo_id,hosted_url=hosted_url).commit()

	#
	#	Set the hosted_id of a photo.
	#	The second bit of synced is set 1
	#
	def setPhotoAddedToSet(self, photo_id):
		self.modifyPhotoByID_UpdateSynced(photo_id, synced=2).commit()

	#
	#	Set the refering_url of a photo.
	#	The third bit of synced is set 1
	#
	def setPhotoReferingURL(self, photo_id, refering_url):
		refering_url="'{}'".format(refering_url)
		self.modifyPhotoByID_UpdateSynced(photo_id,refering_url=refering_url, synced=4).commit()

	#
	#	Modify a photo by values set in kwargs
	#
	#
	def modifyPhotoByID(self, photo_id, **kwargs):
		photo_id="'{}'".format(photo_id)
		return self.modifyRec("photos",{"photo_id":photo_id}, kwargs)

	#
	#	modifyPhotoByID And update synced field
	#
	#
	def modifyPhotoByID_UpdateSynced(self, photo_id, **kwargs):
		photo_id="'{}'".format(photo_id)

		if "synced" in kwargs:
			kwargs["synced"]="synced|{}".format(kwargs["synced"])

		return self.modifyRec("photos",{"photo_id":photo_id}, kwargs)

	#
	#	Remove hosted information about a photo
	#
	#
	def cleanPhotoByID(self, photo_id):
		return self.modifyPhotoByID(photo_id, synced=0, hosted_url="''", refering_url="''", hosted_id="''")



	#
	#	Make a query to update records. 
	#	Table name, update list, and where list are customizable.
	#	The synced field can be set.
	#
	def modifyRec(self, tb_name, where, toModify):
		tmp=["{}={}".format(k,v) for (k,v) in where.items()]
		where_list=" AND ".join(tmp)

		tmp=["{}={}".format(k,v) for (k,v) in toModify.items()]
		update_list=",".join(tmp)

		cmd='''
		UPDATE {tb_name}
		SET {update_list}
		WHERE {where_list}
		'''.format(**locals())
		#print cmd
		return self.makeQuery(cmd)[1]






	#
	#	Get all photos from the photos table 
	#
	def getAllPhotos(self):
		return self.getAllFromTable("photos")

	#
	#	Get all sets from the sets table 
	#
	def getAllSets(self):
		return self.getAllFromTable("sets")

	#
	#	Get all extras from the extras table 
	#
	def getAllExtras(self):
		return self.getAllFromTable("extras")


	#
	#	Get everything from a table 
	#
	def getAllFromTable(self, tb_name):
		cmd="SELECT * FROM "+tb_name
		return self.makeQuery(cmd)[0].fetchall()


	#
	#	Get a photo by its photo_id field 
	#
	def getPhotoByID(self, photo_id):
		photo_id="'{}'".format(photo_id)
		res=self.getRecByField("photos","photo_id",photo_id)
		return res.fetchone()

	#
	#	Get a set by its set_id field 
	#
	def getSetByID(self, set_id):
		set_id="'{}'".format(set_id)
		res=self.getRecByField("sets","set_id",set_id)
		return res.fetchone()

	#
	#	Get all photos with a certain set_id 
	#
	def getPhotosBySetID(self,set_id):
		set_id="'{}'".format(set_id)
		res=self.getRecByField("photos","set_id",set_id)
		return res.fetchall()

	#
	#	Get records by specifying table name, field and value to query 
	#
	def getRecByField(self, tb_name,field_name,value):
		cmd="SELECT * FROM {tb_name} WHERE {field_name}={value}".format(**locals())
		return self.makeQuery(cmd)[0]


	#
	#	Make a query to the db 
	#
	def makeQuery(self, cmd):
		conn=self.conn
		tmp_cursor=conn.cursor()
		tmp_cursor.execute(cmd)
		return tmp_cursor, conn






#
#	Util function
#	Update a base dictionary with another dictionary.
#	Only keys in the base dictionary is accepted  
#
def updatedInput(base, newData):
	keys=base.keys()
	base.update(newData)
	res={k:base[k] for k in base if k in keys}
	return res






if __name__=="__main__":
	print os.path.realpath(".")
	db=CTCPhotoDB()
	print len(db.getAllPhotos())
	'''
	query=CTCPhotoDB()
	query.createTables()
	query.commit()
	'''

	#query.addSet({"set_id":"234125","name":"Bla"})
	#query.addSet({"name":"world"})
	'''
	query.addPhoto({
			"ID":"1234",
			"file_name":"PIC01242",
			"set_id":"1214253",
			"order_in_set":3,
		})
	query.commit()
	'''

	#query.setPhotoHostedID(123456,234567)
	#query.setPhotoHostedURL(123456,"http://flickr.com/abcd.jpg")
	#query.setPhotoAddedToSet(123456,345)
	#query.setPhotoReferingURL(123456,"http://vk.cc/yourls/bla")