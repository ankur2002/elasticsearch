import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/wsgi/elasticsearch")

from elasticsearch_stuff import app as application
application.secret_key = 'AnotherFormApp'
