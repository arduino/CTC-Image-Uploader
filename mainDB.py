import sqlite3, datetime

db_file="maindb.db"

class CTCPhotoDB:
	def __init__(self):
		self.conn=sqlite3.connect(db_file)
		self.conn.row_factory = sqlite3.Row
		self.cursor=self.conn.cursor()

	def createTables(self):
		cmds=['''
		CREATE TABLE IF NOT EXISTS photos(
			ID PRIMARY KEY,
			photo_id CHAR(15),
			file_name CHAR(50),
			set_id INT,
			order_in_set INT,
			hosted_url CHAR(255),
			hosted_id CHAR(15),
			refering_url CHAR(125),
			last_updated DATETIME,
			synced TINYINT
		);
		''',
		'''
		CREATE TABLE IF NOT EXISTS sets(
			set_id PRIMARY KEY,
			name CHAR(125),
			hosted_id CHAR(15),
			state TINYINT
		);
		''']

		for cmd in cmds:
			self.cursor.execute(cmd)

	def addSet(self, pack):
		ipt=self.updatedInput({"set_id":"","name":"","hosted_id":"","state":0},pack)
		cmd='''
		INSERT OR IGNORE INTO sets VALUES
		('{set_id}','{name}','{hosted_id}','{state}')
		'''.format(**ipt)

		#print cmd

		self.cursor.execute(cmd)

	def addPhoto(self,pack):
		basePack={
			"ID":"",
			"photo_id":"",
			"file_name":"",
			"set_id":"",
			"order_in_set":-1,
			"hosted_url":"",
			"hosted_id":"",
			"refering_url":"",
			"last_updated":datetime.datetime.now(),
			"synced":0
		}
		ipt=self.updatedInput(basePack,pack)
		cmd='''
		INSERT OR IGNORE INTO photos VALUES
		('{ID}','{photo_id}','{file_name}','{set_id}',{order_in_set},'{hosted_url}','{hosted_id}','{refering_url}','{last_updated}',{synced})
		'''.format(**ipt)

		#print cmd

		self.cursor.execute(cmd)

	def modifySetByID(self, set_id, **kwargs):
		return self.modifyRec("sets","set_id",set_id, kwargs)

	def modifySetState(self,set_id,state):
		self.modifySetByID(set_id,state=state).commit()

	def modifyPhotoByID(self, photo_id, **kwargs):
		return self.modifyRec("photos","photo_id",photo_id, kwargs)

	def modifyPhotoSynced(self,photo_id,synced, set_id=False):
		cmd='''
		UPDATE photos
		SET synced={synced}
		WHERE photo_id = '{photo_id}'
		'''.format(**locals())
		if set_id:
			cmd=cmd.rstrip()+"AND set_id='{}'".format(set_id)
		return self.makeQuery(cmd)[1].commit()

	def setPhotoHostedID(self, photo_id, hosted_id):
		hosted_id="'{}'".format(hosted_id)
		self.modifyRec("photos","photo_id",photo_id,{"hosted_id":hosted_id,"synced":1}).commit()


	def modifyRec(self, tb_name, id_name, id_val, toModify):
		tmp=["{}={}".format(k,v) for (k,v) in toModify.items()]
		update_list=",".join(tmp)

		cmd='''
		UPDATE {tb_name}
		SET {update_list}
		WHERE {id_name} = '{id_val}'
		'''.format(**locals())
		return self.makeQuery(cmd)[1]


	def commit(self):
		self.conn.commit()

	def getAllPhotos(self):
		return self.getAllFromTable("photos")

	def getAllSets(self):
		return self.getAllFromTable("sets")

	def getAllFromTable(self, tb_name):
		cmd="SELECT * FROM "+tb_name
		return self.makeQuery(cmd)[0].fetchall()

	def getSetByID(self, set_id):
		res=self.getRecByField("sets","set_id",set_id)
		return res.fetchone()

	def getPhotosBySetID(self,set_id):
		res=self.getRecByField("photos","set_id",set_id)
		return res

	def getRecByField(self, tb_name,field_name,value):
		cmd="SELECT * FROM {tb_name} WHERE {field_name}='{value}'".format(**locals())
		return self.makeQuery(cmd)[0]

	def makeQuery(self, cmd):
		#tmp_conn=sqlite3.connect(db_file)
		#tmp_conn.row_factory = sqlite3.Row
		tmp_conn=self.conn
		tmp_cursor=tmp_conn.cursor()
		tmp_cursor.execute(cmd)
		return tmp_cursor, tmp_conn


	def updatedInput(self, base, newData):
		keys=base.keys()
		base.update(newData)
		res={k:base[k] for k in base if k in keys}
		return res


if __name__=="__main__":
	query=CTCPhotoDB()
	query.createTables()
	query.commit()
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