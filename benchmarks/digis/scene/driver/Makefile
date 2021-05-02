SHELL := /bin/bash
THIS_VER := v0.0.1

v2s:
	python vid2scene.py
serve:
	python server.py
redis:
	redis-cli ping || redis-server /usr/local/etc/redis.conf --daemonize yes
run: | redis
	@trap 'kill %1; kill %2' SIGINT; python vid2scene.py & python server.py

