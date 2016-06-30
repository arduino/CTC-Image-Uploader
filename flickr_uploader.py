#import bin.flickr_uploader
import sys
from bin.flickr_uploader.fetchDBData import fetchDBData
from bin.flickr_uploader.MainProcedure import processAll

if __name__=="__main__":
	args=sys.argv

	if "--process" in args:
		processAll()
	elif "--fetchDB" in args:
		print "Some data will be lost with this operation. Press y to continue, other keys to quit."
		cfm=raw_input("")
		if cfm!="y":
			quit()
		fetchDBData()
	else:
		print """
	Please specify an operation.
	--fetchDB
		Update the database with new lightroom category
	--process
		Upload, create flickr sets, generate shortLinks
		"""