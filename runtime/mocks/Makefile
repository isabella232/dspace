.PHONY: gen patch model all delete list

kc := kubectl
driver_dir := ../driver
driver_handler := ./$(KIND)/driver/*.py
digi_config := ./$(KIND)/deploy/*.yaml
build_dir := /tmp/dspace-build-$(KIND)
tutorial_dir := $(GOPATH)/src/digi.dev/tutorial

ifndef IMAGEPULL
override IMAGEPULL = Always
endif

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
	cp ./$(KIND)/driver/handler.py $(driver_dir)/digi; \
	GROUP=$(g) VERSION=$(v) PLURAL=$(r) NAME=$(n) NAMESPACE=$(ns) MOUNTER=$(MOUNTER) \
	python $(driver_dir)/digi

# driver
.PHONY: prepare
prepare:
	rm -r $(build_dir) >/dev/null 2>&1 || true
	mkdir -p $(build_dir)/digi/
	mkdir -p $(build_dir)/deploy/
	cp -r $(driver_dir)/digi $(build_dir) || true
	cp -r $(driver_dir)/deploy $(build_dir) || true
	cp -r $(driver_dir)/requirements.txt $(build_dir) || true

.PHONY: build
build: | prepare gen patch
	cp $(driver_handler) $(build_dir)/digi/ || true
	cd $(build_dir); docker build -t $(registry)/$(KIND):latest -f deploy/image/Dockerfile . || true
	docker push $(registry)/$(KIND):latest || true
	rm -r $(build_dir) || true

# deploy
.PHONY: run stop print
run: | prepare model
	cp $(digi_config) $(build_dir)/deploy || true
	cd $(build_dir)/deploy; mv cr.yaml ./templates; helm install -f values.yaml --set name=$(NAME) $(NAME) . >/dev/null && echo $(NAME) || true
	rm -r $(build_dir) || true
stop:
	helm uninstall $(NAME) >/dev/null && echo $(NAME) || true
print:
	$(kc) get samples sample -oyaml | $(kc) neat

# tutorial
.PHONY: tutorial
tutorial:
	mkdir -p $(tutorial_dir)/workdir || true
	mkdir $(tutorial_dir)/driver || true
	cp -r $(driver_dir)/digi $(tutorial_dir)/driver
	cp -r $(driver_dir)/deploy $(tutorial_dir)/driver
	cp $(driver_dir)/requirements.txt $(tutorial_dir)/driver
	cp gen.py patch.py Makefile $(tutorial_dir)/workdir
