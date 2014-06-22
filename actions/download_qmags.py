#
# A complicated mail action that downloads a Qmags PDF, moves it to ~/Dropbox/Qmags,
# moves the message to the "Downloaded Qmags" IMAP folder and marks it as read.
# 
# TODO: split this action up into reusable atomic actions, that can accept arguments
# to avoid hardcoding paths and values
#

import urllib2

def action(header, message):
    pdfinx  = message.index('Qmags PDF')
    pdfhttp = message.index('http://', pdfinx)
    link = msg.substring(pdfhttp,
                         message.index(' ', pdfhttp))

    r = urllib2.urlopen(urllib2.Request(link))
    text = r.read()

    # extract the download link
    m = re.search('(http://delivery.+?)["|\s]', text)
    if not m:
        return 'NOT FOUND'

    found = m.group(1)
    print "Downloading", found
#    download(found, '~/Dropbox/Qmags')

