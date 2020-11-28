package client

import (
	"encoding/json"
	"fmt"
	_ "log"
	"strings"

	"github.com/tidwall/sjson"

	"digi.dev/digivice/pkg/core"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
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
		// XXX replace sjson with unstructured.unstructured
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
		// validate mount reference
		ok, err := attrExists(tj, pathPrefix)
		if err != nil {
			return fmt.Errorf("unable to find mount %s in %s: %v", pathPrefix, m.Target.SpacedName(), err)
		}
		if !ok {
			return fmt.Errorf("unable to find mount %s in %s", pathPrefix, m.Target.SpacedName())
		}

		// now remove it
		tj, err := sjson.Delete(tj, pathPrefix)
		if err != nil {
			return err
		}
		return c.UpdateFromJson(tj)

	case YIELD:
		// validate mount reference
		ok, err := attrExists(tj, pathPrefix)
		if err != nil {
			return fmt.Errorf("unable to find mount %s in %s: %v", pathPrefix, m.Target.SpacedName(), err)
		}
		if !ok {
			return fmt.Errorf("unable to find mount %s in %s", pathPrefix, m.Target.SpacedName())
		}

		// update its status
		var statusPath string
		statusPath = pathPrefix + core.MountStatusAttrPath

		m.Status = core.MountInactiveStatus
		tj, err = sjson.SetRaw(tj, statusPath, "\""+m.Status+"\"")
		if err != nil {
			return fmt.Errorf("unable to merge json: %v", err)
		}
		return c.UpdateFromJson(tj)
	default:
		return fmt.Errorf("unrecognized mount mode")
	}
}

func attrExists(j, path string) (bool, error) {
	var obj map[string]interface{}
	if err := json.Unmarshal([]byte(j), &obj); err != nil {
		return false, err
	}

	// TBD leaf attr throws an error
	_, ok, err := unstructured.NestedMap(obj, strings.Split(path, ".")...)
	return ok, err
}
