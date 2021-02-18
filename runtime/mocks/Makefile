.PHONY: gen patch run all delete print
kc := kubectl

gen:
	python gen.py $(NAME)
patch:
	python patch.py $(NAME)
run:
	cd ./$(NAME); $(kc) apply -f crd.yaml; $(kc) apply -f cr.yaml
all: | gen patch run
	$(info all)
#delete:

print:
	$(kc) get samples sample -oyaml | $(kc) neat
