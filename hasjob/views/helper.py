from datetime import datetime
from os import path
import bleach
from pytz import utc, timezone
from urllib import quote, quote_plus
from flask import escape, Markup, request, url_for

from hasjob import app
from hasjob.models import agelimit, db, JobCategory, JobPost, JobType, POSTSTATUS
from hasjob.utils import scrubemail

def getposts(basequery=None, sticky=False):
    if basequery is None:
        basequery = JobPost.query
    query = basequery.filter(
            JobPost.status.in_([POSTSTATUS.CONFIRMED, POSTSTATUS.REVIEWED])).filter(
            JobPost.datetime > datetime.utcnow() - agelimit)
    if sticky:
        query = query.order_by(db.desc(JobPost.sticky))
    return query.order_by(db.desc(JobPost.datetime))


def getallposts(order_by=None, desc=False, start=None, limit=None):
    if order_by is None:
        order_by = JobPost.datetime
    filt = JobPost.query.filter(JobPost.status.in_([POSTSTATUS.CONFIRMED, POSTSTATUS.REVIEWED]))
    count = filt.count()
    if desc:
        filt = filt.order_by(db.desc(order_by))
    else:
        filt = filt.order_by(order_by)
    if start is not None:
        filt = filt.offset(start)
    if limit is not None:
        filt = filt.limit(limit)
    return count, filt


@app.template_filter('urlfor')
def url_from_ob(ob):
    if isinstance(ob, JobPost):
        return url_for('jobdetail', hashid=ob.hashid)
    elif isinstance(ob, JobType):
        return url_for('browse_by_type', slug=ob.slug)
    elif isinstance(ob, JobCategory):
        return url_for('browse_by_category', slug=ob.slug)


@app.template_filter('shortdate')
def shortdate(date):
    tz = timezone(app.config['TIMEZONE'])
    return utc.localize(date).astimezone(tz).strftime('%b %e')


@app.template_filter('longdate')
def longdate(date):
    tz = timezone(app.config['TIMEZONE'])
    return utc.localize(date).astimezone(tz).strftime('%B %e, %Y')


@app.template_filter('cleanurl')
def cleanurl(url):
    if url.startswith('http://'):
        url = url[7:]
    elif url.startswith('https://'):
        url = url[8:]
    if url.endswith('/') and url.count('/') == 1:
        # Remove trailing slash if applied to end of domain name
        # but leave it in if it's a path
        url = url[:-1]
    return url


@app.template_filter('urlquote')
def urlquote(data):
    if isinstance(data, unicode):
        return quote(data.encode('utf-8'))
    else:
        return quote(data)


@app.template_filter('urlquoteplus')
def urlquoteplus(data):
    if isinstance(data, unicode):
        return quote_plus(data.encode('utf-8'))
    else:
        return quote_plus(data)


@app.template_filter('scrubemail')
def scrubemail_filter(data, css_junk=''):
    return Markup(scrubemail(unicode(bleach.linkify(bleach.clean(data))), rot13=True, css_junk=css_junk))


@app.template_filter('usessl')
def usessl(url):
    """
    Convert a URL to https:// if SSL is enabled in site config
    """
    if not app.config.get('USE_SSL'):
        return url
    if url.startswith('//'): # //www.example.com/path
        return 'https:' + url
    if url.startswith('/'): # /path
        url = path.join(request.url_root, url[1:])
    if url.startswith('http:'): # http://www.example.com
        url = 'https:' + url[5:]
    return url
