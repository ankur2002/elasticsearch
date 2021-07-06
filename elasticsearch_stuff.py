#!/usr/bin/python3
#@AB feel free to use it however you wish!!
import json,subprocess,shlex
from elasticsearch import Elasticsearch
from flask import Flask,request,render_template,session,jsonify
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap
from wtforms import TextAreaField, SubmitField
from wtforms.validators import Required


class CustomException(Exception): pass

app = Flask(__name__)
#app.config['SECRET_KEY'] = 'AnotherFormApp'
bootstrap = Bootstrap(app)

@app.route('/count/<query>',defaults={'query_index':'solutions_test_crawler','query_type':'doc'})
@app.route('/count/<query_index>/<query_type>/<query>')
def count(query, query_index, query_type):
    """This function runs an elasticsearch count query to get total number of matching documents
       
       Keyword arguments:
       query_index -- set to default to solutions_test_crawler the current index
       query_type -- would indicate the type of a query and it currently defaults to doc
       query -- this is the actual term that is being searched for to get a count
    """

    try:
      index = query_index
      doc_type = query_type
      q = query
      err = ""
      if q == "":
        raise CustomEception()
        res = ""
      else:
        host = ['localhost']
        port = ['9200']
        es = connect(host, port)
        res = es.count(index=query_index,doc_type=query_type,q=query)
        doc_count = res["count"]
        msg  = "There were "+str(doc_count)+ " results retrieved for "+query
    except CustomException:
      err = "Please provide a valid value for the query parameter"
    return render_template('search_result.html', res=msg, err=err)



class SearchForm(FlaskForm):
    term = TextAreaField('What is the term you are searching for?', validators=[Required()])
    submit = SubmitField('Submit')

def validate_term(term):
     """This function simply runs a validate query against the DSL entered in the search_dsl route
        
        returns True if the query is valid else False
     """

     result = {}
     validate = '''
                     curl -XGET http://localhost:9200/solutions_test_crawler/doc/_validate/query -d'
                     %s
                     '     
                ''' % (term)
     args = shlex.split(validate)
     with subprocess.Popen(args, stdout=subprocess.PIPE) as p:
         if p.wait() == 0:
             result = json.loads(p.stdout.read().decode("utf-8"))["valid"]
             return result

@app.route('/search_dsl',methods=['GET','POST'],defaults={'query_index':'solutions_test_crawler','query_type':'doc','size':'50'})
@app.route('/search_dsl/<query_index>/<query_type>/<size>',methods=['GET','POST'])
def search_dsl(query_index, query_type, size):
    """This function runs an elasticsearch search query to match a DSL entered by the end-user
       
       Keyword arguments:
       query_index -- set to default to 'solutions_test_crawler' the current index
       query_type -- would indicate the type of a query and it currently defaults to 'doc'
       query -- this is the actual term that is being searched for to get a count
       size -- that sets the the number of the results returned and currently defaults to '50'
       term -- this is the DSL entered that is passed to the body argument of the elasticsearch search API function
    """
    term = None
    form = SearchForm()
    if form.validate_on_submit():
        term = form.term.data
        try:
          index = query_index
          doc_type = query_type
          #q = query
          size = size
          source = "SOLUTIONS_DESCRIPTION,object.LOCALECODE,SOLUTIONS_TITLE,object.DOCUMENTID"
          q_body = term
          valid = validate_term(term)
          if valid:
            host = ['localhost']
            port = ['9200']
            es = connect(host, port)
            res = es.search(index=query_index,doc_type=query_type,body=q_body,_source_include=source,size=size)
          else:
            res = "That DSL is invalid please correct it"
          if term == "":
              raise CustomEception()
        except CustomException:
            err = "Please provide a valid value for the query parameter"
        else:
            err = ""
            return render_template('search_result.html', res=res, err=err)
    return render_template('search.html', form=form, term=term)


@app.route('/search/<query>',defaults={'query_index':'solutions_test_crawler','query_type':'doc','size':'50'})
@app.route('/search/<query_index>/<query_type>/<size>/<query>')
def search(query, query_index, query_type, size):
    """This function runs an elasticsearch URI search query based on the query entered in the route i.e. search/<query>
       
       Keyword arguments:
       query_index -- set to default to 'solutions_test_crawler' the current index
       query_type -- would indicate the type of a query and it currently defaults to 'doc'
       query -- this is the actual term that is being searched for to get a count
       size -- that sets the the number of the results returned and currently defaults to '50'
       term -- this is the DSL entered that is passed to the body argument of the elasticsearch search API function
    """

    try:
      index = query_index
      doc_type = query_type
      q = query
      size = size
      source = "SOLUTIONS_DESCRIPTION,object.LOCALECODE,SOLUTIONS_TITLE,object.DOCUMENTID"
      host = ['localhost']
      port = ['9200']
      es = connect(host, port)
      res = es.search(index=query_index,doc_type=query_type,q=query,size=size)
      #res = es.search(index=query_index,doc_type=query_type,q=query,_source_include=source,size=size)
      res_json = json.dumps(res, indent=5)
      if q == "":
        raise CustomEception()
    except CustomException:
      err = "Please provide a valid value for the query parameter"
    else:
      err = ""
      return render_template('search_result.html', res=res_json, err=err)

@app.route('/')
def index():
    functions = {'count':['query_index','query_type','query'],'search':['query_index','query_type','query','source_include','size'],'search_dsl':['term','query_index','query_type','source_include','size']}
    terms = {'query_index':'This is the index searched currently that is only solutions_test_crawler defaults:solutions_test_crawler', 'query_type':'Includes doc etc. specified by an analyzer or a json PUT query defaults:doc','query':'The term searched for','size':'This is the number of results you wish to include defaults:50','term':'This is the query dsl based query instead of a single term'}
    return render_template('index.html', functions=functions, terms=terms)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def page_not_found(e):
    return render_template('404.html'), 500

def connect(host,port=None):
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





