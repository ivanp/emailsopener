import csv
from cookielib import CookieJar
import json
import os
import random
import re
#import urllib, httplib
#from urllib import request
#import urllib
#from urllib.error import HTTPError
#from urllib2.Request import Request
import urllib
import urllib2
#from urlparse import urljoin
#from urlparse import urlparse
import urlparse
from pyquery import PyQuery
from utils import serializeArray

__author__ = 'dude'

emails = list(csv.reader(open('emails.txt', 'r')))
proxies = list(csv.reader(open('proxies.txt', 'r')))

for email in emails:
    email, password = email
    name, provider = email.lower().split("@")

    proxy = proxies[random.randint(0, len(proxies) - 1)]
    cookie = CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie), urllib2.HTTPRedirectHandler(),
        urllib2.ProxyHandler({'socks': proxy})
    )
    urllib2.install_opener(opener)
    opener.addheaders = [('User-Agent',
                          'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:13.0) Gecko/20100101 Firefox/13.0.1')]

    #region AOL.COM
    if provider == 'aol.com':
        print "Loggining into AOL ..."
        html = urllib2.urlopen('http://mail.aol.com').read().decode('utf-8')

        loginForm = PyQuery(html).find('#formCreds')
        action = loginForm.attr("action")

        loginData = dict(serializeArray(loginForm))
        loginData['loginId'] = name
        loginData['password'] = password

        redirect = False
        try:
            urllib2.urlopen(action, urllib.urlencode(loginData).encode())
        except HTTPError as e:
            redirect = e.geturl()

        if not redirect:
            print "Can't login into AOL.COM with: %s - %s" % (name, password) 
        else:
            print "Logged in [Application PATH: %s ]. Collecting new messages ..." % redirect

            auth = cookie._cookies['.mail.aol.com']['/']['Auth'].value
            auth = dict(x.split(":") if len(x.split(":")) == 2 else (x, '') for x in auth.split("&"))

            RPCURL = 'http://mail.aol.com' + os.path.dirname(os.path.dirname(redirect)) + "/common/rpc/RPC.aspx?"

            req = urllib2.Request(RPCURL + urllib.urlencode({
                'user': auth['uid'],
                'transport': 'xmlhttp',
                'r': random.randint(10000000000, 9000000000000),
                'a': 'GetMessageList'
            }), (
                'requests=%5B%7B%22folder%22%3A%22Inbox%22%2C%22start%22%3A0%2C%22count%22%3A100%2C%22indexStart%22%3A0%2C%22indexMax%22%3A100%2C%22index%22%3Atrue%2C%22info%22%3Atrue%2C%22rows%22%3Atrue%2C%22sort%22%3A%22received%22%2C%22tcs%22%3Afalse%2C%22sortDir%22%3A%22descending%22%2C%22subSearch%22%3A%22%22%2C%22seen%22%3A%5B%5D%2C%22screenName%22%3A%22' + name + '%22%2C%22returnfoldername%22%3Afalse%2C%22action%22%3A%22GetMessageList%22%7D%5D&automatic=false'
                ).encode()
            )
            req.add_header('X-Requested-With', 'XMLHttpRequest')

            jsonresult = urllib2.urlopen(req).read().decode('utf-8')
            result = json.loads(jsonresult)
            if result[0]['isSuccess']:
                rows = result[0]['rows']

                newMessages = result[0]['folders'][0][6]
                if newMessages:
                    print 'Found %s new messages. Marking them as opened ...' % newMessages

                    ids = []
                    for message in rows:
                        if message[8] == 1:
                            continue

                        id = message[0]
                        sender = "%s <%s>" % (message[2], message[1])
                        subject = message[3]

                        print '\t"%s": %s' % (sender, subject)
                        ids.append(id)

                    check = {
                        'automatic': False,
                        'requests': json.dumps([
                                {"messageAction": "seen", "folder": "Inbox", "uids": {"Inbox": ids}, "xuids": {},
                                 "checkUndo": False, "screenName": name, "isUndoAction": False,
                                 "isSearchAction": False, "action": "MessageAction"}])
                    }

                    if ids:
                        ids = urllib.parse.quote(json.dumps(ids))
                        check = 'requests=%5B%7B%22messageAction%22%3A%22seen%22%2C%22folder%22%3A%22Inbox%22%2C%22uids%22%3A%7B%22Inbox%22%3A' + ids + '%7D%2C%22xuids%22%3A%7B%7D%2C%22checkUndo%22%3Afalse%2C%22screenName%22%3A%22phpduderu%22%2C%22isUndoAction%22%3Afalse%2C%22isSearchAction%22%3Afalse%2C%22action%22%3A%22MessageAction%22%7D%5D&automatic=false'

                        req = urllib2.Request(RPCURL + urllib.parse.urlencode({
                            'user': auth['uid'],
                            'transport': 'xmlhttp',
                            'a': 'MessageAction'
                        }), check.encode())
                        req.add_header('X-Requested-With', 'XMLHttpRequest')

                        res = json.loads(urllib2.urlopen(req).read().decode('utf-8'))
                        print "Checking as readed ... %s" % 'Done' if res[0]['isSuccess'] else 'Error'
                else:
                    print 'Not found new messages'
            else:
                print "Can't load messages list"

    #endregion
    #region HotMail
    elif provider == 'hotmail.com':
        print "Loggining into HotMail ...", 

        html = urllib2.urlopen('http://mail.live.com/').read().decode('utf-8')
        ppft = re.search('<input type="hidden" name="PPFT" id="[^"]+" value="([^"]+)"', html).group(1)
        action = re.search("var srf_uPost='([^']+)'", html).group(1)

        postData = dict(re.findall("var srf_s([^=]+)='([^']+)';", html))

        html = urllib2.urlopen(action, urllib.urlencode({
            'PPFT': ppft,
            'login': email,
            'passwd': password,
            }).encode()).read().decode('utf-8')

        if html.find('replace("http://mail.live.com/default.aspx?rru=inbox")') == -1:
            print "Can't login into HotMail with: %s - %s" % (name, password)
        else:
        #        cookie.clear(domain='.mail.live.com', path='/', name='KVC')
            cookie.clear(domain='.live.com', path='/', name='WLSSC')

            print 'Logged in. Redirecting to email inbox...', 
            nexturl = 'http://mail.live.com/default.aspx?rru=inbox'
            inboxURL = ''
            while nexturl:
                try:
                    print '.', 
                    #                    print "\tRedirecting to %s" % nexturl
                    req = urllib2.urlopen(nexturl)
                    html = req.read().decode('utf-8')
                    inboxURL = req.url
                    nexturl = False
                except urllib2.HTTPError as e:
                    print e.read()
                    nexturl = urlparse.urljoin(nexturl, e.headers['location'])

            print "Done"

            fppURL = urlparse.urljoin(inboxURL, '/mail/mail.fpp') + "?"

            cfg = dict(re.findall('(\w+)\s*:\s*"([^"]+)"', re.search('fppCfg:(\{.*?\})', html).group(1)))
            sessID = urllib.unquote(cfg['SessionId'])
            authUser = urllib.unquote(cfg['AuthUser'])

            print 'Fetching new messages list ... ',
            get = {
                'cnmn': 'Microsoft.Msn.Hotmail.Ui.Fpp.MailBox.GetInboxData',
                'ptid': 0,
                'a': sessID,
                'au': authUser
            }

            listURL = fppURL + urllib.urlencode(get)

            mt = re.search('OptionsWriter.aspx\x3f(.*?)"', html).group(1)
            mt = urlparse.parse_qs(json.loads('"' + mt + '"'))['mt'][0]

            postData = 'cn=Microsoft.Msn.Hotmail.Ui.Fpp.MailBox&mn=GetInboxData&d=true,false,true,{%2200000000-0000-0000-0000-000000000001%22,null,,FirstPage,5,1,null,null,null,Date,false,false,%22%22,null,-1,-1,false,Off,-1,null,null,true},false,null&v=1'
            req = urllib2.Request(listURL, postData.encode())
            req.add_header('X-Requested-With', 'XMLHttpRequest')
            req.add_header('X-Fpp-Command', 0)
            req.add_header('Mt', mt)
            lst = urllib2.urlopen(req).read().decode('utf-8')

            lst = lst.replace('\\"', '"')
            lst = "".join(re.findall('<tr class="ia_hc[^>]+>.*?</tr>', lst))
            lst = PyQuery(lst)

            newMessages = len(lst.find("tr.ia_hc.mlUnrd"))
            print "Found %s new messages." % newMessages

            for l in lst.find("tr.ia_hc.mlUnrd"):
                l = PyQuery(l)

                mailID = l.attr("id")
                mad = l.attr("mad")
                mailFrom = l.find("span[email]").attr("email")

                postData = 'cn=Microsoft.Msn.Hotmail.Ui.Fpp.MailBox&mn=GetInboxData&d=false,false,false,null,true,{%22' + mailID +\
                           '%22,false,-1,null,{%22' + urllib.parse.quote(mad.replace("|",
                    '\|')) + '%22},null,%2200000000-0000-0000-0000-000000000001%22,true,%22' + urllib.parse.quote(
                    mailFrom) + '%22}&v=1'

                print "\tOpening %s [ID:%s]..." % (mailFrom, mailID), 
                req = urllib2.Request(listURL, postData.encode())
                req.add_header('X-Requested-With', 'XMLHttpRequest')
                req.add_header('X-Fpp-Command', 0)
                req.add_header('Mt', mt)
                res = urllib2.urlopen(req).read().decode('utf-8')

                print 'Done'

    #endregion

    #region Yahoo
    elif provider == 'yahoo.com':
        print 'Loggining into yahoo ...'

        html = urllib2.urlopen('http://mail.yahoo.com/').read().decode('utf-8')
        loginForm = PyQuery(html).find('#login_form')

        action = loginForm.attr('action')
        loginData = dict(serializeArray(loginForm))

        loginData['login'] = email
        loginData['passwd'] = password

        html = urllib2.urlopen(action, urllib.urlencode(loginData).encode()).read().decode('utf-8')

        if html.find('<meta http-equiv="Refresh" content="0;') == -1:
            print "Can't login into Yahoo with: %s - %s" % (name, password)
        else:
            print 'Logged in! Checking new messages ...'

            mailurl = re.search('url=(.*?)">', html).group(1)

            html = urllib2.urlopen(mailurl).read().decode('utf-8')
            wssid = re.search('wssid:"(.*?)"', html).group(1)

            rpcurl = urlparse.urljoin(mailurl, '/ws/mail/v2.0/formrpc') + "?"

            result = urllib2.urlopen(rpcurl + urllib.urlencode({
                'appid': 'YahooMailNeo',
                'm': 'ListFolders',
                'o': 'json',
                'resetMessengerUnseen': 'true',
                'wssid': wssid
            })).read().decode('utf-8')

            result = json.loads(result)
            newMessages = list(filter(lambda x: x['folderInfo']['name'] == 'Inbox', result['folder']))[0]['unread']

            if not newMessages:
                print "Not found new messages"
            else:
                print "Found %s new messages." % newMessages

                result = urllib2.urlopen(rpcurl + urllib.urlencode({
                    'appid': 'YahooMailNeo',
                    'm': 'ListMessages',
                    'fid': 'Inbox',
                    'groupBy': 'unRead',
                    'o': 'json',
                    'numInfo': 50,
                    'sortKey': 'date',
                    'sortOrder': 'down',
                    'startInfo': 0,
                    'wssid': wssid
                })).read().decode('utf-8')

                result = json.loads(result)

                rpcurl = urlparse.urljoin(mailurl, '/ws/mail/v2.0/jsonrpc') + "?"
                for msg in result['messageInfo']:
                    if msg['flags']['isRead']:
                        continue

                    print '\tOpening %s<%s>: %s... ' % msg['from']['name'], msg['from']['email'], msg['subject'], 

                    mid = msg['mid']
                    post = '{"method":"FlagMessages","params":[{"fid":"Inbox","mid":["' + mid + '"],"setFlags":{"read":1},"enableRetry":true}]}'

                    result = urllib2.urlopen(rpcurl + urllib.urlencode({
                        'appid': 'YahooMailNeo',
                        'm': 'FlagMessages',
                        'wssid': wssid
                    }), post.encode()).read().decode('utf-8')

                    result = json.loads(result)
                    print 'Done!' if not result['error'] else ('Error: ' + result['error'])

    #endregion

    elif provider == 'gmail.com':
        print "Loggining into Gmail ... ", 

        html = urllib2.urlopen('https://mail.google.com/mail/').read().decode('utf-8')

        pq = PyQuery(html).find('#gaia_loginform')

        action = pq.attr("action")
        loginData = dict(serializeArray(pq))
        loginData['Passwd'] = password
        loginData['Email'] = email

        req = urllib2.urlopen(action, urllib.urlencode(loginData).encode())
        html = req.read().decode('utf-8')

        if html.find('name="application-url" content="https://mail.google.com/mail"') == -1:
            print "Can't login into Gmail.com with: %s - %s" % (name, password)
        else:
            print 'Logged in!',

            html = urllib2.urlopen('https://mail.google.com/mail/?ui=html&zy=c').read().decode('utf-8')

            baseURL = PyQuery(html).find('base').attr('href')

            newMessages = PyQuery(html).find('tr[bgcolor="#ffffff"]')

            if not len(newMessages):
                print 'Not found new messages'
            else:
                print 'Found %s new messages' % len(newMessages)

                mids = []
                for msg in newMessages:
                    msg = PyQuery(msg)

                    print('\tOpening "%s": %s...' %
                          (msg.find("td").eq(1).text(), msg.find("td").eq(2).find('b').text()))
                    mids.append('t=' + msg.find('input[type="checkbox"]').val())

                submit = PyQuery(html).find("form[name=f]").attr('action')

                mids.append('tact=rd')
                mids.append('nvp_tbu_go=Go')
                mids.append('redir=?&')
                mids.append('bact=')

                process = urllib2.urlopen(baseURL + "?" + submit, '&'.join(mids).encode()).read().decode('utf-8')
