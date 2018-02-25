import os, sys

#########
# Mocks #
#########

# TODO: implement here the mocks that enable the tests in tail_reader_test.py to run

def fake_get_filesize(filename):
	return 2
	

class FakeFileHandler():
	
	def __init__(self, fake_content):
		self.fake_content = fake_content

	def __enter__(self):
		return self

	def __exit__(self, type, value, traceback):
		pass

	def stat(self,filename):
		return self

	def st_size(filename):
		return os.stat(filename).st_size



class FakeFileReader():
	"""docstring for FakeFileReader"""
	def __init__(self):
		pass

	def read_file_from_tail(self,data,filename,numlines,stopline,bufsize):
		pass

	def assert_called_with(self,data,filename,numlines,stopline,bufsize):
		try:
			if stopline != None:
				stopline = stopline + "\n"
			return self.read_file_from_tail(data,filename,numlines,stopline,bufsize)
		except FileNotFoundError:
			return None

	def __iter__(self):
		yield self



		
		
		
		
