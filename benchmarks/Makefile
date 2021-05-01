# Steps to run a benchmark:
# - make stop
# - start leaf digivices
# - make graph (create the digi-graph)
# - make run (start benchmarks)
.PHONY: graph stop run
graph:
	# construct digi-graph
	# assume the lamp is already running
	cd digis; \
	dq run room room-test && sleep 10 && \
	dq mount lamp-test room-test; sleep 1; \
	kubectl get rooms room-test -oyaml | kubectl neat
stop:
	cd digis; \
	dq stop room room-test || true
	dq stop lamp lamp-test || true
run:
	python cli.py
