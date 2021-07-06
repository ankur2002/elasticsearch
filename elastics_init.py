import xmltodict
from os import path, walk, makedirs
import pickle, requests, urllib3
import certifi, urllib.request
from urllib.error import URLError, HTTPError
import re, time, shutil
import datetime


class ExceptionFound(Exception): pass


def collect_files(dir, good_files=[], bad_files=[]):
	files = [root + '/' + file for root, dirs, files in walk(dir) for file in files if file.endswith('.xml')]
	if good_files or bad_files:
		subset = [file for file in files if file not in bad_files]
		return subset
	else:
		return files


def parse_files(files, bad_files=[]):
	valid_sol_files = []
	doc_data = {}
	for file in files:
		doc, bad_files = xmltodict_file(file, bad_files)
		if doc:
			if validate_files(doc) and check_enddttm_files(doc):
				get_doc_data(file, doc, doc_data, valid_sol_files, bad_files)
	return valid_sol_files, doc_data, bad_files


def get_doc_data(file, doc, doc_data, valid_sol_files, bad_files):
	regex = "^(?=.*PROD_(.*))(?!.*PROD_DELETED).*"
	for item in doc['CONTENT']['CATEGORIES']['REFERENCE_KEY']:
		res = re.search(regex, item)
		if res:
			product = res.group(0)
			sln = doc['CONTENT']['DOCUMENTID']
			locale = doc['CONTENT']['LOCALECODE']
			doc_data[file] = (sln, product, locale)
			valid_sol_files.append(file)
			break
		else:
			bad_files.append(file)


def xmltodict_file(file, bad_files=[]):
	with open(file, 'r') as file_read2:
		try:
			doc = xmltodict.parse(file_read2.read().strip())
		except xmltodict.expat.ExpatError:
			print(file, 'has a problem skipping it')
			bad_files.append(file)
			doc = []
		return doc, bad_files


def validate_files(doc):
	if type(doc['CONTENT']['SECURITY']['USERGROUP']) is list:
		for item in doc['CONTENT']['SECURITY']['USERGROUP']:
			if doc['CONTENT']['TYPE'] == 'SOLUTIONS' and doc['CONTENT']['VIEWS']['NAME'] == 'Yahoo Customer Support' and \
							item['NAME'] == 'Customer':
				return True
	else:
		if doc['CONTENT']['TYPE'] == 'SOLUTIONS' and doc['CONTENT']['VIEWS']['NAME'] == 'Yahoo Customer Support' and \
						doc['CONTENT']['SECURITY']['USERGROUP']['NAME'] == 'Customer':
			return True
	return False


def check_mtime_files(files):
	updated_files = []
	for file in files:
		if ((time.time() - path.getmtime(file)) < 24 * 60 * 60):
			updated_files.append(file)
			files.remove(file)
	return updated_files


def check_url_files(files, doc_data):
	count = 0
	for file in files:
		#print(doc_data[file])
		sln, product, locale = doc_data[file]
		# sln_name = file.split('/')[5]
		url_source = "https://help.yahoo.com/helpws/v1/articles/" + sln + "?locale=" + locale + "&product=" + product + "&platform=PLAT_WEB&format=json"
		# url_source = "https://help.yahoo.com/kb/"+sln_name+'.html'
		print('Checking for ', url_source, str(datetime.datetime.now().time()))
		r = requests.get(url_source, allow_redirects=False, stream=True)
		#http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where(), maxsize=1)
		#r2 = http.request('GET', url_source)
		#print(r2.status, str(datetime.datetime.now().time()))
		try:
			code = urllib.request.urlopen(url_source).getcode()
			print(str(datetime.datetime.now().time()))
		except URLError as e:
			print(e.code)
		print(r.status_code, str(datetime.datetime.now().time()))
		if r.status_code != 200:
			files.remove(file)
		else:
			count = count + 1
	return files, count


def check_enddttm_files(doc):
	if 'ENDDATE' in doc['CONTENT'].keys():
		enddate = doc['CONTENT']['ENDDATE']
		file_endtime = time.mktime(time.strptime(enddate, "%d/%m/%Y"))
		if file_endtime < time.time():
			return False
		elif file_endtime > time.time():
			return True
		# Need to add a check if enddate is same as today then we need to check endtime!!
	else:
		return True


def copy_files(files, dest):
	for file in files:
		dir_name = path.dirname(file)
		dir_path = re.sub('(.*)/SOLUTIONS/', '', dir_name)
		dest_path = dest + dir_path
		try:
			if not path.exists(dest_path):
				makedirs(dest_path)
			shutil.copy(file, dest_path)
		except ExceptionFound:
			print('Could not copy ', file, ' to path ', dest_path)
		else:
			print('Copying ', file, ' to ', dest_path)


if __name__ == '__main__':
	global good_files, bad_files
	dest = '/tmp/es/'
	dir_path = '/home/abhatia/SOLUTIONS'
	pickle_bfilepath = dir_path + "/es_invalid_files.pickle"
	pickle_gfilepath = dir_path + "/es_valid_files.pickle"
	if not path.exists(pickle_bfilepath) and not path.exists(pickle_gfilepath):
		good_files, bad_files = [], []
		files = collect_files(dir_path)
		valid_files, doc_data, bad_files = parse_files(files, bad_files)
		with open(pickle_gfilepath, 'wb') as pick_gw:
			pickle.dump(valid_files, pick_gw)
		with open(pickle_bfilepath, 'wb') as pick_bw:
			pickle.dump(bad_files, pick_bw)
		print('Found ', len(valid_files), ' valid files, now checking for a valid URL')

		good_files, count = check_url_files(valid_files, doc_data)
		print('Found ', len(bad_files), 'bad files and ', count, ' good files')
		copy_files(good_files, dest)
	else:
		with open(pickle_gfilepath, 'rb') as pick_gr:
			good_files = pickle.load(pick_gr)
		with open(pickle_bfilepath, 'rb') as pick_br:
			bad_files = pickle.load(pick_br)
		files = collect_files(dir_path, good_files, bad_files)
		valid_files,doc_data, bad_files = parse_files(files, bad_files)
		updated_files = check_mtime_files(valid_files)
		for file in updated_files:
			valid_files.append(file)
		files,count =  check_url_files(valid_files, doc_data)
		print('Found ', len(bad_files), 'bad files and ', count, ' good files')
		copy_files(files, dest)
