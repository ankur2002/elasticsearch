# elasticsearch
The templates and static directories contain the css files and the bootstrap templates used to create the site. 

The wsgi script is just that, a wsgi hook into the actual script i.e. elasticsearch_stuff.py which generates flask routes for certian parts of the elasticsearch-api. 

And esearch_init.py is the initial script I run to extract the external customer facing solutions xml files from the solutions directory and it also checks the individual URL's and the timestamps on the files etc. The final set is then copied over to /tmp/es for fscrawler to crawl and index.
