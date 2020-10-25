package client

import (
	"fmt"
	"log"
	"strings"

	"github.com/tidwall/sjson"

	"digi.dev/digivice/pkg/core"
)

// Mounter contains methods to perform a mount
type Mounter struct {
	Source core.Auri `json:"source,omitempty"`
	Target core.Auri `json:"target,omitempty"`
	Mode   string     `json:"mode,omitempty"`
	Status string     `json:"status,omitempty"`
}

func NewMounter(s, t, mode string) (*Mounter, error) {
	si, err := core.ParseAuri(s)
	if err != nil {
		return nil, err
	}

	ti, err := core.ParseAuri(t)
	if err != nil {
		return nil, err
	}

	return &Mounter{
		Source: si,
		Target: ti,
		Mode:   mode,
		Status: core.ActiveStatus,
	}, nil
}

// Mount updates the target digivice's model with a mount reference to the source digivice;
// a mount is successful iff 1. source and target are compatible; 2. caller has sufficient
// access rights.
func (m *Mounter) Mount() error {
	c, err := NewClient()
	if err != nil {
		return fmt.Errorf("unable to create k8s client: %v", err)
	}

	// source digivice
	_, err = c.GetResourceJson(&m.Source)
	if err != nil {
		return fmt.Errorf("%v", err)
	}

	// target digivice
	tj, err := c.GetResourceJson(&m.Target)
	if err != nil {
		return fmt.Errorf("%v", err)
	}
	//log.Printf("%s\n%s", sj, tj)

	doMount := func() error {
		log.Println("mount: do", m.Mode)

		// add the mount reference (Kind.SpacedName) to the target
		//path := strings.Join([]string{common.MountRefPrefix, m.Source.Kind.Name, m.Source.SpacedName()}, ".")
		pathPrefix := []string{core.MountRefPrefix, m.Source.Kind.Plural(), m.Source.SpacedName().String()}

		// set mode
		modePath := strings.Join(append(pathPrefix, "mode"), ".")
		tj, err := sjson.SetRaw(tj, modePath, "\""+m.Mode+"\"")
		if err != nil {
			return fmt.Errorf("unable to merge json: %v", err)
		}

		// set status
		statusPath := strings.Join(append(pathPrefix, "status"), ".")
		tj, err = sjson.SetRaw(tj, statusPath, "\""+m.Status+"\"")
		if err != nil {
			return fmt.Errorf("unable to merge json: %v", err)
		}

		log.Printf("mount: %v", tj)

		// update the target
		return c.UpdateFromJson(tj, m.Target.Namespace)
	}

	return doMount()
}

func (m *Mounter) Unmount() error {
	// TODO
	return nil
}

func (m *Mounter) Yield() error {
	// TODO
	return nil
}
