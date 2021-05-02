# Steps to run a benchmark:
# - make stop
# - start leaf digivices
# - make graph (create the digi-graph)
# - NAME={file_name}.py make run (start benchmarks)

ifndef NAME
override NAME = lamp
endif

.PHONY: graph stop run
measure:
	cd digis/measure; \
	kubectl apply -f crd.yaml; \
	kubectl apply -f test/cr.yaml
graph: | measure
	# construct digi-graph
	# assume the lamp is already running
	cd digis; \
	dq run room room-test && sleep 5 && \
	dq mount lamp-test room-test; sleep 1; \
	kubectl get rooms room-test -oyaml | kubectl neat
stop:
	cd digis; \
	dq stop room room-test || true; \
	dq stop lamp lamp-test || true; \
	cd measure/test; kubectl delete -f cr.yaml || true
run: | measure
	python $(NAME).py
