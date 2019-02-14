server:
	FLASK_DEBUG=1 flask run

pytest:
	watching_testrunner -- pytest todotxt_test.py

jstests:
	npx karma start karma.conf.js

docker:
	docker-compose up

docker-build:
	# use DOCKER_BUILDKIT=1  to switch to buildkit backed buidling 
	# @see https://github.com/moby/buildkit/blob/master/frontend/dockerfile/docs/experimental.md
	docker-compose up --build

docker-debug-shell:
	docker-compose exec backend bash

docker-shell:
	docker run --interactive --tty --rm task-tracker_backend /bin/bash
