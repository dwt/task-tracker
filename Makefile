server:
	(sleep 2; open http://127.0.0.1:5000/)&
	FLASK_DEBUG=1 flask run

pytest:
	watching_testrunner -- pytest todotxt_test.py

jstests:
	(sleep 2; open http://0.0.0.0:9876/)&
	npx karma start karma.conf.js
