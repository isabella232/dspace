module digi.dev/digivice/cmd

go 1.15

require (
	digi.dev/digivice v0.0.0
    digi.dev/digivice/runtime/sync v0.0.0
    github.com/spf13/cobra v1.1.1
)

replace (
	digi.dev/digivice v0.0.0 => ../
	digi.dev/digivice/runtime/sync v0.0.0 => ../runtime/sync
	k8s.io/client-go => k8s.io/client-go v0.18.2
)
