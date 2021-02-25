.PHONY: gen patch run all delete print

kc := kubectl
registry := silveryfu
driver_templates := ../driver
deploy_templates := ../driver/deploy
driver_handler := ./$(KIND)/driver/*.py
digivice_config := ./$(KIND)/deploy/*.yaml
build_dir := /tmp/dspace-build-$(KIND)

# model
gen:
	python gen.py $(KIND)
patch:
	python patch.py $(KIND)
model:
	cd ./$(KIND); $(kc) apply -f crd.yaml
model-all: | gen patch model
	$(info model)
delete:
	cd ./$(KIND); $(kc) delete -f crd.yaml

# driver
.PHONY: build
build:
	cp -r $(driver_templates) $(build_dir)
	cp $(driver_handler) $(build_dir)
	cd $(build_dir); docker build -t $(registry)/$(KIND):latest -f deploy/image/Dockerfile .
	docker push $(registry)/$(KIND):latest
	rm -r $(build_dir)

# deploy
.PHONY: run stop
run: | model
	cp -r $(deploy_templates) $(build_dir)
	cp $(digivice_config) $(build_dir)
	cd $(build_dir); mv cr.yaml ./templates; helm install -f values.yaml --set name=$(NAME) $(NAME) .
	rm -r $(build_dir)
stop:
	helm uninstall $(NAME)
print:
	$(kc) get samples sample -oyaml | $(kc) neat
