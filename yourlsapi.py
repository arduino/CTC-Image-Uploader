import requests
import time,hashlib,json

from configs import yourls_signature, yourls_URL

yourlsTimer=0
signature=""


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
