.PHONY: build run
REPO=silveryfu
build:
	operator-sdk generate k8s || exit 1
	operator-sdk generate crds || exit 1

	docker login
	operator-sdk build $(REPO)/syncer:latest
	docker push $(REPO)/syncer:latest
	sed -e 's/{{REPO}}/$(REPO)/g' ./deploy/actor.template > ./deploy/actor.yaml
stop:
	kubectl delete -f deploy/crds/ || true
	kubectl delete -f deploy/ || true
run: | stop
	kubectl create -f deploy/crds/
	kubectl create -f deploy/
mock:
	kubectl apply -f deploy/mocks/crds/ || true
	kubectl apply -f deploy/mocks/crs/ || true
test: | run mock
	$(info test on mocks)
log:
	kubectl logs $(shell kubectl get pods --selector=name=syncer -o jsonpath="{.items[*].metadata.name}")
all: | build test
	$(info build and run)
