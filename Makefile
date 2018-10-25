server:
	FLASK_DEBUG=1 flask run

pytest:
	watching_testrunner -- pytest todotxt_test.py

jstests:
	npx karma start karma.conf.js
