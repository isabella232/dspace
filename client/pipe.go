package client

import "digi.dev/digivice/pkg/core"

type Piper struct {
	Source core.Auri `json:"source,omitempty"`
	Target core.Auri `json:"target,omitempty"`
}

func NewPiper(s, t string) (*Piper, error) {
	return nil, nil
}

func (p *Piper) Pipe() error {
	return nil
}

func (m *Mounter) Unpipe() error {
	return nil
}
