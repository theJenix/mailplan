#
# A complicated mail action that downloads a Qmags PDF, moves it to ~/Dropbox/Qmags,
# moves the message to the "Downloaded Qmags" IMAP folder and marks it as read.
# 
# TODO: split this action up into reusable atomic actions, that can accept arguments
# to avoid hardcoding paths and values
#

import urllib2
import re
from util import download

def action(header, message, ops):

    # <a href=3D"http://www.qmags.com/R/?i=3D2374a8&=\ne=3D2278786&doi=3D52256083&uk=3D2FE1171B167127DE131449DD111622C5882FF14=\nF115.htm" target=3D"_blank">Download</a>'

    oneline = message.replace('=\r\n', '').replace('=3D', '=')

    m = re.search('(http://[^"]*)[^>]*>(?=Download)', oneline)

    if not m:
        m = re.search('(http://[^"]*)[^>]*>(?=DOWNLOAD)', oneline)

    if not m:
        m = re.search('(http://[^"]*)[^>]*>(?=Click here</a> to download)', oneline) #, re.DOTALL)

    if not m:
        # Qmags PDF....http://"
        pdfinx  = message.index('Qmags PDF')
        ro = re.compile('(http://.+?)["|\s]')
    
        m = ro.search(message, pdfinx)

    link = m.group(1)
    print "Opening link", link
    r = urllib2.urlopen(urllib2.Request(link))
    text = r.read()

    # TODO: check for error/expired link, and move to expired folder
    # extract the download link
    m = re.search('(http://delivery.+?)["|\s]', text)
    if not m:
        ops.move('Downloaded Qmags/Error')
        return 'NOT FOUND'

    found = m.group(1)
    print "Downloading", found
    download(found, '~/Dropbox/Qmags')
    ops.move('Downloaded Qmags')
