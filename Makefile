# tbd: digi.dev/dac
IMAGE="silveryfu/dac"
NAME="dspace"
DAC="./runtime/admission"

# Build the development docker image
.PHONY: dac-build
dac-build:
	docker build -t $(IMAGE) -f $(DAC)/Dockerfile ./

.PHONY: dac-push
dac-push:
	docker push $(IMAGE)

.PHONY: dac
dac: | dac-build dac-push
	$(info build and push)

.PHONY: deploy stop log
deploy:
	kubectl apply -f $(DAC)/cmd/deploy
stop:
	kubectl delete -f $(DAC)/cmd/deploy || true
log:
	kubectl logs $(shell kubectl get pods --selector=app=dspace-webhook -o jsonpath="{.items[*].metadata.name}")

.PHONY: all
all: | dac stop deploy log
	$(info build and deploy)

.PHONY: certs
certs:
	cd $(DAC); ./create-certs.sh default ${NAME}
