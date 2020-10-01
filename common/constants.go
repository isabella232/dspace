package common

var (
	DefaultNamespace = "default"

	// mount labels
	MountRefPrefix   = "mounts"
	YieldRefPrefix   = "yields"
	ExposeMode = "expose"
	HideMode = "hide"
	DefaultMode = ExposeMode

	// connect labels
	SourceRefPrefix = "sources"
	SinkRefPrefix = "sinks"
)
