.PHONY: test build
test:
	kubectl apply -f ./test/*crd.yaml
	kubectl apply -f ./test/*cr.yaml
build:
	docker build -t silveryfu/imitator:latest -f deploy/Dockerfile .
	docker push silveryfu/imitator:latest
