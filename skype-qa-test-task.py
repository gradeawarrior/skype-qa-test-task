#!/usr/bin/env python
#
# Author: Peter Salas
# Project Name: Skype QA Test Task
# Date: 05/05/2010
# Description:
#	A quick illustration of a test program and a list of tests which verifies the correctness of the
#	libcurl API. The goal of this task is to verify that the libcurl API works correctly as expected.
#
#	Specifically, the program is passed a test script through stdin with each line containing at least one URL:
#
#		<startTime> <URL> <method> [<verification_type> <value> <..>]
#
#	Where:
#		* startTime - 		The time to start the fetch in ms (relative to the start of the program, so 
#					0 means immediately on program start).
#		* URL - 		The url of object to fetch
#		* method -		The method to execute. [GET|POST|PUT|DELETE]
#		* verification_type -	Basic verification parameters. Currently supports 'code' for the response_code,
#					but can easily be extended
#		* value -		The value to verify based on the verification_type. Example: if verification_type='code'
#					and value='200', then we expect that the response_code of the object fetch is '200'
#	

import sys
import getopt
import pycurl
import time
import os.path
from operator import attrgetter

_debug = 0
_redirect = 0
types = { 'code':1 }
wr_buf = ''
def write_data( buf ):
	global wr_buf
	wr_buf += buf

def usage():
    print "Usage: skype-qa-test-task.py -f FILE"
    print "\n\t -f/--file FILE\t\tTest input file"
    print "\t -r\t\t\tEnable Follow Redirects"
    print "\t -d\t\t\tEnable Debugging"
    print "\t -h/--help"

def dummy():
	return 0

#################
# Request Class #
#################

class Request:
    """
	A basic Request type class that encapsulates a basic request type and maps to pycurl library.
    """

    def __init__(self, sleep, url, method, type, value):
	"""
	__init__():
		functions as class constructor.

	Parameters:
		sleep - The sleep time in milliseconds from start of script
		url - The url object to fetch
		type - (Optional) An optional validation type (e.g. 'code')
		value - (Optional) An optional validation value (e.g. '200')
	"""

	self.url = url
	self.sleep = sleep
	self.method = method

	self.type = type
	if not type: self.type = 'code'					## Default type='code'
	assert(types.has_key(self.type))

	self.value = value
	if not value: self.value = '200'				## Default value='200'

	self.curl = pycurl.Curl()
	self.curl.setopt(pycurl.URL, self.url)				## URL
    	if _redirect: self.curl.setopt(pycurl.FOLLOWLOCATION, 1) 	## Follow Redirects
    	self.curl.setopt(pycurl.WRITEFUNCTION, write_data)		## Write to a buffer instead of straight to STDOUT
    	self.curl.setopt(pycurl.CONNECTTIMEOUT_MS, 10000)		## Timeout in milliseconds

	## Change the method [GET|POST|PUT|DELETE]
	if "POST" in self.method:
	    self.curl.setopt(pycurl.POST, 1)
	    self.curl.setopt(pycurl.POSTFIELDS, "")
	elif "PUT" in self.method:
	    self.curl.setopt(pycurl.UPLOAD, 1)
	    #self.curl.setopt(pycurl.READDATA, self.dummy)
	    #self.curl.setopt(pycurl.INFILESIZE, 0)
	elif "DELETE" in self.method: self.curl.setopt(pycurl.CUSTOMREQUEST, "DELETE")

    def print_result(self):
	"""
	print_result():
		Formats the output for printing

	Parameters:
		None

	Returns:
		A formatted string
	"""

	error = self.curl.getinfo(pycurl.OS_ERRNO)
	#if _debug: print "ERRNO: %s" % (error)

	code = self.curl.getinfo(pycurl.HTTP_CODE)
	total_time = self.curl.getinfo(pycurl.TOTAL_TIME)
	string_6 =  "%s %s %s %s %s %s"
	string_5 =  "%s %s %s %s %s"

	if error:
	    return string_6 % ("FAIL", "ERROR", self.url, code, self.method, self.curl.strerror(error))
	elif ((self.type == "code") and (code == 0)):
	    return string_6 % ("FAIL", "ERROR", self.url, code,  self.method, "No Server Response")
        elif ((self.type == "code") and (str(self.value) != str(code))):
	    return string_6 % ("FAIL", total_time, self.url, code, self.method, "Expected %s response code" % (self.value))
	else:
	    return string_5 % ("PASS", total_time, self.url, code, self.method)

    def debug(self):
	return "%s %s" % (self.sleep, self.url)

    def dummy(self):
	return 0


########
# Main #
########


def main(argv):
    """
	main():
		The main logic of the program. All logic goes through here
    """

    file = ""
    try:                                
        opts, args = getopt.getopt(argv, "hf:dr", ["help", "file="])	## Define CLI inputs
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt == '-d':
	    global _debug
            _debug = 1
        elif opt == '-r':
	    global _redirect
            _redirect = 1
        elif opt in ("-f", "--file"):
            file = arg

    source = "".join(args)
    ## Double check that file is valid
    if (not os.path.isfile(file)):
        print "[ERROR] File not defined or does not exist!\n"
	usage()
	sys.exit(1)

    requests = read_file(file)		## (1) Parse file and save as request reference
    print_requests(requests)		## (2) Print the requests. Only visible if _debug enabled
    execute(requests)			## (3) Execute requests
    format_results(requests)		## (4) Formats the results from step 3


####################
# Helper Functions #
####################


def read_file(file):
    """read_file() processes the specified file and stores in internal structure"""

    rfile = {}
    line_num = 1

    ## Iterate through file
    if _debug: print "RAW File contents:"
    infile = open(file,"r")
    while infile:
        line = infile.readline()
	line = line.rstrip("\n")
	if not line: break

	if _debug: print "%d: %s" % (line_num, line)
	line_num += 1
	if "#" in line: continue

        args = line.split()
	if len(args) > 0: key = args[0]
	args.reverse()
	if rfile.has_key(float(key)):
	    if len(args) >= 5: rfile[float(key)].append(Request(args.pop(), args.pop(), args.pop(), args.pop(), args.pop()))
	    elif len(args) >= 3: rfile[float(key)].append(Request(args.pop(), args.pop(), args.pop(), None, None))
	    else: continue
	else:
	    if len(args) >= 5: rfile[float(key)] = [Request(args.pop(), args.pop(), args.pop(), args.pop(), args.pop())]
	    elif len(args) >= 3: rfile[float(key)] = [Request(args.pop(), args.pop(), args.pop(), None, None)]
	    else: continue;
	#rfile.append(Request(args[0], args[1]))

    return rfile

def get_sorted_keys(requests):
    """get_sorted_keys() sorts the keys of the requests, which is essentially sorting the startTime values"""

    keys = requests.keys()
    keys.sort()
    return keys

def format_results(requests):
    """format_results() Iterates through the requests and prints the line number + the request results"""

    keys = get_sorted_keys(requests)
    index = 1
    
    print "\nResults:"
    for key in keys:
	for request in requests[key]:
	    print "%s %s" % (index, request.print_result())
	    index += 1
    
def print_requests(requests):
    """print_requests() a simple debugging function for verifying request structure"""

    if not _debug: return
    keys = get_sorted_keys(requests)

    print "\nIn Memory Structure:"
    print "{"
    for key in keys:
	print "  %s:[" % (key)
        for request in requests[key]:
		print "    (%s, %s)," % (key, request.url)
	print "  ]"
    print "}\n"

def execute(requests):
    """execute() all requests"""

    keys = get_sorted_keys(requests)
    running_time = 0
    m = pycurl.CurlMulti()

    if _debug: print "keys:", keys
    while (keys or num_requests):					## (1) Sort by startTime and loop while there's
	num_requests = len(requests)					#	i) There are still startTime buckets to process
	key = None							#	ii)There are still requests to process
	if len(keys): key = keys.pop(0)

	if key:
	    sleep_time = (float(key)/1000) - running_time		## (2) Calculate sleep_time based on current running_time (in seconds)
	    running_time += sleep_time
	    print "Sleeping for %s sec - %s requests to add handle to Curl MultiObject" % (sleep_time, len(requests[key]))
	    time.sleep(sleep_time)					## (3) Sleep the specified milliseconds

	    for request in requests[key]:
	        m.add_handle(request.curl)				## (4) Add all requests scheduled start after specified milliseconds
									#      to the curl multiobject
	num_requests = execute_multiobject(num_requests, m)		## (5) Execute multiobject process
    
def execute_multiobject(num_handles, multiobject):
    """Execute Curl Multiline and return the current num_handles"""

    ret = multiobject.select(1.0)
    if ret == -1: return 0
    while 1:
        ret, num_handles = multiobject.perform()
        if ret != pycurl.E_CALL_MULTI_PERFORM: break

    return num_handles


if __name__ == "__main__":
    main(sys.argv[1:])
