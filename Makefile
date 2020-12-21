server:
	FLASK_DEBUG=1 FLASK_RELOAD=1 flask run

pytest:
	watching_testrunner -- pytest todotxt_test.py

jstests:
	npx karma start karma.conf.js

docker:
	COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose up --force-recreate --abort-on-container-exit

docker-build: 
	COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose up --build --force-recreate --abort-on-container-exit

docker-shell-attach:
	# requires a running container started via `make docker` or `make docker-build`
	docker-compose exec backend bash

docker-shell-create:
	# works wether the container is runnig or not
	docker-compose run backend bash
	# docker run --interactive --tty --rm task-tracker_backend /bin/bash

docker-clean:
	# this gets rid of the runtime overlay but retains all the images
	# docker-compose down
	# this is a pretty complete clean, but retainns the base images so they don't have to be downloaded again for a rebuild
	docker-compose down --rmi local --volumes
	# this gets rid of all files from other projects / contexts too
	# docker system prune --filter until=12h --all --force
