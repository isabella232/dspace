package core

var (
	DefaultNamespace = "default"

	// mount labels
	// XXX move to core
	MountRefPrefix = "mounts"

	ExposeMode     = "expose"
	HideMode       = "hide"
	DefaultMode    = ExposeMode

	// XXX MountActiveStatus
	ActiveStatus   = "active"
	InactiveStatus = "inactive"

	// connect labels
	// XXX remove; no need pipe references
	SourceRefPrefix = "sources"
	SinkRefPrefix   = "sinks"
)
