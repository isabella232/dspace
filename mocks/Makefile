ifndef WORKDIR
override WORKDIR = .
endif

ifndef IMAGEPULL
override IMAGEPULL = Always
endif

ifndef REPO
override REPO = silveryfu
endif

ifndef DIGIREPO
override DIGIREPO = /tmp/digirepo
endif

ifndef TAG
override TAG = mock
endif

ifndef IMAGEBUILD
override IMAGEBUILD =
endif


kc := kubectl
digi_src := $(GOPATH)/src/digi.dev/dspace
driver_dir := $(digi_src)/runtime/driver
driver_handler := $(WORKDIR)/$(KIND)/driver/*
digi_config := $(WORKDIR)/$(KIND)/deploy/*.yaml
build_dir := /tmp/dspace-build-$(KIND)-$(TAG)
tutorial_dir := $(GOPATH)/src/digi.dev/tutorial

# model
.PHONY: gen patch model all delete list
gen:
	python gen.py $(KIND)
patch:
	python patch.py $(KIND)
model:
	cd $(WORKDIR)/$(KIND) && $(kc) apply -f crd.yaml >/dev/null
all: | gen patch model
	$(info model)
delete:
	cd $(WORKDIR)/$(KIND) >/dev/null 2>&1; $(kc) delete -f crd.yaml 2>/dev/null || true
	rm -r $(WORKDIR)/$(KIND) >/dev/null 2>&1 || true

list:
	ls -d */ 2> /dev/null | sed 's#/##'

.PHONY: test

# test configs
g := $(TAG).digi.dev
v := v1
r := $(KIND)s
n := $(KIND)-test
ns := default

test: | model all
	cd $(WORKDIR)/$(KIND)/test; $(kc) delete $(KIND) $(n); $(kc) apply -f cr.yaml
	GROUP=$(g) VERSION=$(v) PLURAL=$(r) NAME=$(n) NAMESPACE=$(ns) MOUNTER=$(MOUNTER) \
	python $(WORKDIR)/$(KIND)/driver/handler.py

# driver
.PHONY: prepare
prepare:
	rm -r $(build_dir) >/dev/null 2>&1 || true
	mkdir -p $(build_dir)/deploy/
	rsync -r $(driver_dir) $(build_dir) || true
	rsync -r $(driver_dir)/deploy $(build_dir) || true
	rsync -r $(driver_dir)/requirements.txt $(build_dir) || true

.PHONY: build
build: | prepare gen patch
	rsync $(driver_handler) $(build_dir)/ || true
	cd $(build_dir); docker build $(IMAGEBUILD) -t $(REPO)/$(KIND):$(TAG) -f deploy/image/Dockerfile . || true
	docker push $(REPO)/$(KIND):$(TAG)|| true
	rm -r $(build_dir) || true

# image
.PHONY: push pull
push:
	mkdir $(DIGIREPO) >/dev/null 2>&1 || true
	cd $(WORKDIR); tar czf $(KIND).gz $(KIND) && mv $(KIND).gz $(DIGIREPO)/ >/dev/null || true
pull:
	cd $(WORKDIR); rsync $(DIGIREPO)/$(KIND).gz . && tar xzf $(KIND).gz && rm $(KIND).gz > /dev/null

# deploy
.PHONY: run stop print
run: | stop prepare model
	rsync $(digi_config) $(build_dir)/deploy || true
	cd $(build_dir)/deploy; mv cr.yaml ./templates; \
	helm install -f values.yaml --set name=$(NAME) $(NAME) . >/dev/null || true \
	rm -r $(build_dir) || true
stop:
	$(kc) delete $(KIND) $(NAME) >/dev/null 2>&1 || true
	helm uninstall $(NAME) >/dev/null 2>&1 || true
print:
	$(kc) get samples sample -oyaml | $(kc) neat

# debug
.PHONY: log
log:
	kubectl logs `kubectl get pod --field-selector status.phase=Running \
	-l name=$(NAME) -oname --sort-by=.status.startTime | tail -n1 | sed "s/^.\{4\}//"`

# tutorial
.PHONY: tutorial
tutorial:
	mkdir -p $(tutorial_dir)/workdir || true
	rsync gen.py patch.py Makefile $(tutorial_dir)/workdir

.PHONY: dq bench
dq:
	mkdir -p ~/.dq/
	rsync gen.py patch.py Makefile ~/.dq/
bench:
	rsync gen.py patch.py Makefile ../../benchmarks/digis/
