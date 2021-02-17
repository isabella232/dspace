.PHONY: gen patch run all print
kc := kubectl

gen:
	python gen.py $(NAME)
patch:
	python patch.py $(NAME)
run:
	cd ./$(NAME); $(kc) apply -f crd.yaml; $(kc) apply -f cr.yaml
all: | gen patch run
	$(info all)

print:
	$(kc) get mocklamps mock-lamp-1 -oyaml | $(kc) neat
