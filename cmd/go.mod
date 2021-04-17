module digi.dev/dspace/cmd

go 1.15

require (
	digi.dev/dspace v0.0.0
	digi.dev/dspace/runtime/sync v0.0.0
	github.com/spf13/cobra v1.1.1
	gopkg.in/yaml.v2 v2.4.0
	k8s.io/apimachinery v0.18.6
)

replace (
	digi.dev/dspace v0.0.0 => ../
	digi.dev/dspace/runtime/sync v0.0.0 => ../runtime/sync
	k8s.io/client-go => k8s.io/client-go v0.18.2
)
