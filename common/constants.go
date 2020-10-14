package common

var (
	DefaultNamespace = "default"

	// mount labels
	MountRefPrefix = "mounts"
	ExposeMode     = "expose"
	HideMode       = "hide"
	DefaultMode    = ExposeMode
	ActiveStatus   = "active"
	InActiveStatus = "inactive"

	// pipe labels
	PipeSourceMode = "source"
	PipeSinkMode   = "sink"

	// connect labels
	SourceRefPrefix = "sources"
	SinkRefPrefix   = "sinks"
)
