import urllib2
import shutil
import urlparse
import os

def download(url, targetPath='.', fileName=None):
    def getFileName(url,openUrl):
        if 'Content-Disposition' in openUrl.info():
            # If the response has Content-Disposition, try to get filename from it
            cd = dict(map(
                lambda x: x.strip().split('=') if '=' in x else (x.strip(),''),
                openUrl.info()['Content-Disposition'].split(';')))
            if 'filename' in cd:
                filename = cd['filename'].strip("\"'")
                if filename: return filename
        # if no filename was found above, parse it out of the final URL.
        return os.path.basename(urlparse.urlsplit(openUrl.url)[2])

    r = urllib2.urlopen(urllib2.Request(url))
    try:
        fileName = fileName or getFileName(url,r)
        print "Downloading file", fileName
        with open(targetPath + '/' + fileName, 'wb') as f:
            shutil.copyfileobj(r,f)
    finally:
        r.close()

#download("http://delivery.qmags.com/d/DefaultV1.aspx?cid=2278792&cid=2278792&sessionID=62F241AABEF354FBE0F124CF3&editionID=18887&platform=A&")
