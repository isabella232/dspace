.PHONY: lamp print
kc := kubectl

lamp:
	cd ./mock_lamp; $(kc) apply -f crd.yaml; $(kc) apply -f cr.yaml
room:
	cd ./mock_room; $(kc) apply -f crd.yaml; $(kc) apply -f cr.yaml
print:
	$(kc) get mocklamps mock-lamp-1 -oyaml | $(kc) neat
