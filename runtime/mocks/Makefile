.PHONY: gen patch model all delete list

kc := kubectl
driver_templates := ../driver/digi
deploy_templates := ../driver/deploy
driver_handler := ./$(KIND)/driver/*.py
digivice_config := ./$(KIND)/deploy/*.yaml
build_dir := /tmp/dspace-build-$(KIND)
tutorial_dir := $(GOPATH)/src/digi.dev/tutorial

ifndef REPO
override REPO = silveryfu
endif
registry := $(REPO)

# model
gen:
	python gen.py $(KIND)
patch:
	python patch.py $(KIND)
model:
	cd ./$(KIND) && $(kc) apply -f crd.yaml >/dev/null
all: | gen patch model
	$(info model)
delete:
	cd ./$(KIND) >/dev/null 2>&1; $(kc) delete -f crd.yaml 2>/dev/null || true
	rm -r ./$(KIND) >/dev/null 2>&1 && echo $(KIND) removed || true

list:
	ls -d */ 2> /dev/null | sed 's#/##'

.PHONY: test

# test configs
g := mock.digi.dev
v := v1
r := $(KIND)s
n := $(KIND)-test
ns := default

test: | model all
	cd ./$(KIND)/test; $(kc) delete $(KIND) $(n); $(kc) apply -f cr.yaml
	# TBD: allow standalone handler
	cp ./$(KIND)/driver/handler.py $(driver_templates); \
	GROUP=$(g) VERSION=$(v) PLURAL=$(r) NAME=$(n) NAMESPACE=$(ns) MOUNTER=$(MOUNTER) \
	python $(driver_templates)

# driver
.PHONY: build
build: | gen patch
	rm -r $(build_dir) >/dev/null 2>&1 || true
	cp -r $(driver_templates)/ $(build_dir) || true
	cp $(driver_handler) $(build_dir) || true
	cd $(build_dir); docker build -t $(registry)/$(KIND):latest -f deploy/image/Dockerfile . || true
	docker push $(registry)/$(KIND):latest || true
	rm -r $(build_dir) || true

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
print:
	$(kc) get samples sample -oyaml | $(kc) neat

# tutorial
.PHONY: tutorial
tutorial:
	mkdir -p $(tutorial_dir)/workdir || true
	cp -r ../driver $(tutorial_dir)
	cp gen.py patch.py Makefile $(tutorial_dir)/workdir
