#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os.path import join,exists
from pysqlite2 import dbapi2 as sqlite
from mod_python import apache,util

BASE=join('/','p1','astronomi2009','rapport')
DBNAME=join(BASE,'rapport.db')

def opendb(name=DBNAME):
    if not exists(name):
        return 'Give me a database to open, please!'
    else:
        conn=sqlite.connect(name)
        curs=conn.cursor()
        return conn,curs

def filecontent(filename,base=BASE):
    f=open(join(base,filename))
    content=f.read()
    f.close()
    return content

def cursum(curs):
    return curs.execute('SELECT sum(antal) from rapp').fetchone()

def listreports(curs):
    result='<p>Summa deltagare hittills: %s</p>'%cursum(curs)
    result+='<p><table border="1"><tr><td>Datum </td><td>Antal </td><td>Var</td><td>Vad</td><td>Arrang&ouml;r</td><td>ID</td></tr>'
    wanted='day,mon,id,var,vad,vem,antal'
    all=curs.execute('SELECT %s FROM rapp ORDER BY mon,day'%wanted).fetchall()
    for day,mon,id,var,vad,vem,antal in all:
        result+='<tr><td>%02d/%02d </td><td>%s </td><td>%s </td><td>%s </td><td>%s </td><td>%s </td></tr>'%(day,mon,antal,var,vad,vem,id)
    result+='</table></p>'
    return result

def fixdates(curs):
    all=curs.execute('SELECT id,dat FROM rapp;').fetchall()
    for id,dat in all:
	day,mon=dat.split('/')
	curs.execute('UPDATE rapp SET day=%s WHERE id=%s;'%(day,id))
	curs.execute('UPDATE rapp SET mon=%s WHERE id=%s;'%(mon,id))
    return 'fine!'

def newrep(curs):
    result='<p>Hittills har <strong>%s</strong> bes&ouml;kare rapporterats (<a href="/rapport/list">till listan</a>).</p>'%cursum(curs)
    result+='<p>Fyll i nedan f&ouml;r att rapportera.<br/>Alla f&auml;lt &auml;r obligatoriska.<br/>Epost beh&ouml;vs f&ouml;r att undvika spam och f&ouml;r att kunna reda ut eventuella oklarheter. Adressen visas inte offentligt.</p>'
    result+='<p><FORM ACTION="/rapport/nrep" METHOD="POST">'
    result+='Hur m&aring;nga tittade genom teleskop? <input type="text" maxlength="3" size="3" value="" name="antal" /><br/>'
    result+='Datum (dd/mm): <input type="text" maxlength="5" size="5" value="" name="dat" /><br/>'
    result+='Var? <input type="text" maxlength="256" size="50" value="" name="var" /><br/>'
    result+='Vad? <input type="text" maxlength="256" size="50" value="" name="vad" /><br/>'
    result+='Arrang&ouml;r? <input type="text" maxlength="256" size="50" value="" name="vem" /><br/>'
    result+='Epost (kontaktperson/ansvarige): <input type="text" maxlength="256" size="50" value="" name="email" /><br/><br/>'
    result+='<INPUT TYPE="submit" VALUE="SKICKA" NAME="send">'
    result+='</p>'

    return result

def faildata(data):
    if not data[0]: return 'Antal saknas.'
    try: int(data[0])
    except: return 'Antal &auml;r inte en siffra.'
    if not data[1]: return 'Arrang&ouml;r saknas.'
    if not data[2]: return 'Plats saknas.'
    if not data[3]: return 'F&auml;ltet "Vad" saknas.'
    if not ('@' in data[4] and '.' in data[4]): return 'Epost saknas eller har fel format.'
    if not '/' in data[5]: return 'Fel datumsformat: anv&auml;nd dd/mm'

def fixenc(data):
    try: return data.decode('utf8')
    except:
        try: return data.decode('latin1')
        except: return data.decode('ascii','replace')

def nrep(form,curs):
    wanted='antal,vem,var,vad,email,dat'.split(',')
    data=[fixenc(form.getfirst(i,'')) for i in wanted]
    error=faildata(data)
    day,mon=data[-1].split('/')
    data.append(day)
    data.append(mon)
    data.append(2009)
    if not error:
        curs.execute('INSERT INTO rapp VALUES (null, ?, ?, ?, ?, ?, ?, ?, ?, ?)',data)
        return 'Tack! Uppgifterna har sparats.<br/> Ladda inte om den h&auml;r sidan utan anv&auml;nd bak&aring;t-knappen f&ouml;r att rapportera mer. <br/>'
    else:
        return u'F&ouml;ljande fel uppstod: <strong>%s</strong> <br/> Anv&auml;nd bak&aring;t-knappen i din webbl&auml;sare och f&ouml;rs&ouml;k igen.'%error

def testuser(req):
    if (req.user=='admin') or (req.user=='astro'): return True
    else: return False


def handler(req):
    req.content_type = "text/html"
    form=util.FieldStorage(req)

    req.write(filecontent('head'))

    conn,curs=opendb()

    wanted=req.uri[1:]
    if wanted == 'rapport/':       result=newrep(curs)
    elif wanted == 'rapport/nrep': result=nrep(form,curs)
    elif wanted == 'rapport/list': result=listreports(curs)
    elif wanted == 'rapport/fixdates': result=fixdates(curs)
    else:                          result='Don\'t know what to do with %s'%req.uri

    conn.commit()
    conn.close()

    req.write(result.encode('ascii','xmlcharrefreplace'))

    req.write(filecontent('foot'))

    return apache.OK
