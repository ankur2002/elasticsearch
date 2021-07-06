import xmltodict
from os import path,walk,makedirs
import pickle,requests
import re,time,shutil


class ExceptionFound(Exception): pass


def collect_files(dir, good_files=[], bad_files=[]):
	files = [root + '/' + file for root, dirs, files in walk(dir) for file in files if file.endswith('.xml')]
	if good_files or bad_files:
		subset = [file for file in files if file not in good_files and file not in bad_files]
		return subset
	else:
		return files


def parse_files(files, bad_files=[]):
	valid_sol_files = []
	for file in files:
		with open(file, 'r') as file_read2:
			try:
				doc = xmltodict.parse(file_read2.read().strip())
				if doc and validate_files(doc):
					valid_sol_files.append(file)
				else:
					bad_files.append(file)
			except xmltodict.expat.ExpatError:
				print(file, 'has a problem skipping it')
				bad_files.append(file)
				continue
	return valid_sol_files, bad_files


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

def check_url_files(files):
	for file in files:
		sln_name = path.basename(file)
		url_source = "https://help.yahoo.com/"+sln_name
		r = requests.get(url_source,allow_redirects=True)
		files.remove(file) if r.status_code != 200 else print('Solutions ',sln_name, ' returned ',r.status_code)
	return files

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
			print('Copying ',file,' to ',dest_path)

if __name__ == '__main__':
	global good_files, bad_files
	dest = '/tmp/es/'
	dir_path = '/home/abhatia/SOLUTIONS'
	pickle_bfilepath = dir_path + "/es_invalid_files.pickle"
	pickle_gfilepath = dir_path + "/es_valid_files.pickle"
	if not path.exists(pickle_bfilepath) and not path.exists(pickle_gfilepath):
		good_files, bad_files = [], []
		files = collect_files(dir_path)
		valid_files, bad_files = parse_files(files, bad_files)
		with open(pickle_gfilepath, 'wb') as pick_gw:
			pickle.dump(valid_files, pick_gw)
		with open(pickle_bfilepath, 'wb') as pick_bw:
			pickle.dump(bad_files, pick_bw)
		files = check_url_files(files)
		copy_files(valid_files,dest)
	else:
		with open(pickle_gfilepath, 'rb') as pick_gr:
			good_files = pickle.load(pick_gr)
		with open(pickle_bfilepath, 'rb') as pick_br:
			bad_files = pickle.load(pick_br)
		files = collect_files(dir_path, good_files, bad_files)
		updated_files = check_mtime_files(good_files)
		for file in updated_files:
			files.append(file)
		files = check_url_files(files)
		copy_files(files,dest)
