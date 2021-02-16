.PHONY: mock test build run stop all quick
build:
	docker build -t silveryfu/imitator:latest -f build/Dockerfile .
	docker push silveryfu/imitator:latest
run:
	kubectl apply -f ./deploy/crds
	kubectl apply -f ./deploy
stop:
	kubectl delete -f ./deploy/crds || true
	kubectl delete -f ./deploy || true
mock:
	kubectl apply -f ./deploy/mocks/crd
	kubectl apply -f ./deploy/mocks/cr
delete-mock:
	kubectl delete -f ./deploy/mocks/cr || true
test: | stop delete-mock run mock
	$(info test on mocks)
all: | stop build delete-mock run mock
	$(info all)
quick:
	kopf run handlers.py --verbose
