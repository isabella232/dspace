.PHONY: gen patch model all delete list

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
	cd ./$(KIND); $(kc) apply -f crd.yaml >/dev/null
all: | gen patch
	$(info model)
delete:
	cd ./$(KIND); $(kc) delete -f crd.yaml
list:
	ls -d */ | sed 's#/##'

.PHONY: test

# test configs
g := mock.digi.dev
v := v1
r := $(KIND)s
n := $(KIND)-test
ns := default

test: | model all
	cd ./$(KIND)/test; $(kc) delete $(KIND) $(n); $(kc) apply -f cr.yaml
	cp ./$(KIND)/driver/handler.py $(driver_templates); \
	GROUP=$(g) VERSION=$(v) PLURAL=$(r) NAME=$(n) NAMESPACE=$(ns) MOUNTER=$(MOUNTER) \
	python $(driver_templates)/driver.py

# driver
.PHONY: build
build:
	rm -r $(build_dir) >/dev/null 2>&1 || true
	cp -r $(driver_templates)/* $(build_dir)
	cp $(driver_handler) $(build_dir)
	cd $(build_dir); docker build -t $(registry)/$(KIND):latest -f deploy/image/Dockerfile .
	docker push $(registry)/$(KIND):latest
	rm -r $(build_dir)

# deploy
.PHONY: run stop print
run: | model
	rm -r $(build_dir) >/dev/null 2>&1 || true
	cp -r $(deploy_templates) $(build_dir) || true
	cp $(digivice_config) $(build_dir) || true
	cd $(build_dir); mv cr.yaml ./templates; helm install -f values.yaml --set name=$(NAME) $(NAME) . >/dev/null && echo $(NAME) || true
	rm -r $(build_dir) || true
stop:
	helm uninstall $(NAME) >/dev/null && echo $(NAME) || true
stop:
print:
	$(kc) get samples sample -oyaml | $(kc) neat
