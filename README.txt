Objective: Develop a test program and a list of tests which verifies the correctness of the
libcurl API.

The goal of this task is to verify that the libcurl API works correctly as expected. Specifically,
your program will be passed a test script through stdin with each line containing at least one
URL:

<startTime> <URL> <...>

Where
	•	startTime is the time to start the fetch in ms (relative to the start of the program, so 0 means immediately on program start).
	•	URL is the URL of the object fetched. Only http URLs will be given and there will be no whitespace in the URL.
	•	more parameters which are required or helpful for the results of your tests

So the line

500 http://www.skype.com/

specifies that 500ms after the program begins execution, a fetch of http://www.skype.com/ should be initiated.

Your program should read lines until it encounters a blank line or EOF.

One test line is considered to have passed if the expected result (fetched page, expected error code) was met. If the result does not meet the expectation it is considered to have failed.

Your program must be implemented in C++ or in Python. If you choose C++ it must perform these fetches using the libcurl-multi interface described at http://curl.haxx.se/libcurl/c/libcurl-multi.html. If you choose Python it must perform these fetches using the CurlMulti Object which is described at http://pycurl.sourceforge.net/doc/curlmultiobject.html.

When finished, your program should output one line of results per fetch, formatted as:

<line#> <PASS|FAIL> <fetchTime> <URL> <libcurl explanation>
<...>

Where
	•	line# is the line number the fetch was found on (counting from 0)
	•	PASS|FAIL is the text PASS or FAIL
	•	fetchTime is the amount of time in ms the operation took to complete (or report an error)
	•	URL is the URL that was specified in the input
	•	libcurl explanation is the output of curl_easy_strerror() on the returned status
	•	... potentially more parameters which are helpful to understand the test result

Your solution should consist of the source code of your program to execute the tests as well
as a single test script (as described above) to be fed into your program to demonstrate its
abilities.

