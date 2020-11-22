package core

var (
	MountRefPrefix      = "mounts"
	DefaultMountMode    = "expose"

	MountActiveStatus   = "active"
	MountInactiveStatus = "inactive"

	_ = MountActiveStatus
	_ = MountInactiveStatus

	MountAttrPath = ".spec.mounts"
	MountAttrPathSlice = AttrPathSlice(MountAttrPath)

	_ = MountAttrPath
	_ = MountAttrPathSlice
)

type Mount struct {
	Source Auri   `json:"source,omitempty"`
	Target Auri   `json:"target,omitempty"`

	Mode   string `json:"mode,omitempty"`
	Status string `json:"status,omitempty"`
}

// mounts indexed by the target's namespaced name
type MountRefs map[string]Mount