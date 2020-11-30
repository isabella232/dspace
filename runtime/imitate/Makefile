.PHONY: test build
test:
	kubectl apply -f ./test/*crd.yaml
	kubectl apply -f ./test/*cr.yaml
build:
	docker build -t silveryfu/imitator:latest -f build/Dockerfile .
	docker push silveryfu/imitator:latest
run:
	kubectl apply -f ./deploy
stop:
	kubectl delete -f ./deploy
