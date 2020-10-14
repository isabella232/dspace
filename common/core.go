package common

type MountRef struct {
	Mode   string `json:"mode,omitempty"`
	Status string `json:"status,omitempty"`
}

type PipeRef struct {
	Type string `json:"type,omitempty"`
}
