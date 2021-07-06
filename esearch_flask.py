#!/usr/bin/env python3
#@AB feel free to use it however you wish!!

from elasticsearch import Elasticsearch
from flask import Flask, request


app = Flask(__name__)

def create_app():
    return app


class CustomException(Exception): pass

@app.route('/count/<query_index>/<query_type>/<query>')
def count(query_index,query_type,query):
    index = query_index
    doc_type = query_type 
    q = query
    try:   
      res = es.count(index=query_index,doc_type=query_type,q=query)
      if index== "" or q == "":
        raise CustomEception()
    except CustomException:
      print("Please provide a valid value for both the index and the query parameters")  
    else:
      return '<h1>Your result is %s</h1>'  % res
       




def connect(host,port='Null'):
    host_port = []
    if isinstance(host,dict) and port =='':
        for key,value in dict.items():
            host_port.append(key+':'+value)
    else:
       if isinstance(host,list) and isinstance(port,list):
           for hosts,ports in zip(host,port):
               host_port.append(hosts+':'+ports)
       elif isinstance(host,list) and not isinstance(port,list):
           for hosts in host:
               host_port.append(hosts+':'+port)
       elif host and port:
           host_port.append(host+':'+port)
       else:
           return('Error')
       es = Elasticsearch(host_port)
       return(es)






if __name__ == "__main__":
    host = ['localhost']
    port = ['9200']
    es = connect(host,port)
    #count = count(es,['solutions_test_crawler'],'doc','messenger')
    app = create_app()
    app.run(host='0.0.0.0',port=80)
    #print(count)


