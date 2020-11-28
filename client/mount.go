package client

import (
	"fmt"
	_ "log"
	"strings"

	"github.com/tidwall/sjson"

	"digi.dev/digivice/pkg/core"
)

const (
	MOUNT = iota
	UNMOUNT
	YIELD
)

// Mounter contains methods to perform a mount
type Mounter struct {
	core.Mount
	Op int
}

func NewMounter(s, t, mode string) (*Mounter, error) {
	si, err := ParseAuri(s)
	if err != nil {
		return nil, err
	}

	ti, err := ParseAuri(t)
	if err != nil {
		return nil, err
	}

	return &Mounter{
		Mount:
		core.Mount{
			Source: si,
			Target: ti,
			Mode:   mode,
			Status: core.MountActiveStatus,
		},
	}, nil
}

func (m *Mounter) Do() error {
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

	pathPrefix := fmt.Sprintf("%s%c%s%c%s", strings.TrimLeft(core.MountAttrPath, "."), '.', m.Source.Kind.Name, '.', m.Source.SpacedName().String())

	switch m.Op {
	case MOUNT:
		// updates the target digivice's model with a mount reference to the source digivice;
		// a mount is successful iff 1. source and target are compatible; 2. caller has sufficient
		// access rights.
		var modePath, statusPath string
		modePath = pathPrefix + core.MountModeAttrPath
		statusPath = pathPrefix + core.MountStatusAttrPath

		// set mode and status
		tj, err := sjson.SetRaw(tj, modePath, "\""+m.Mode+"\"")
		if err != nil {
			return fmt.Errorf("unable to merge json: %v", err)
		}

		tj, err = sjson.SetRaw(tj, statusPath, "\""+m.Status+"\"")
		if err != nil {
			return fmt.Errorf("unable to merge json: %v", err)
		}
		//log.Printf("mount: %v", tj)

		return c.UpdateFromJson(tj)
	case UNMOUNT:
		tj, err := sjson.Delete(tj, pathPrefix)
		if err != nil {
			return err
		}
		return c.UpdateFromJson(tj)
	case YIELD:
	default:
		return fmt.Errorf("unrecognized mount mode: %s", m.Op)
	}
	return nil
}
