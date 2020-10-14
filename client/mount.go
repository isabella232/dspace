package client

import (
	"fmt"
	"log"
	"strings"

	"github.com/tidwall/sjson"

	"digi.dev/digivice/client/config"
	"digi.dev/digivice/common"
)

// Mounter contains methods to perform a mount
type Mounter struct {
	Source *ID    `json:"source,omitempty"`
	Target *ID    `json:"target,omitempty"`
	Mode   string `json:"mode,omitempty"`
	Status string `json:"status,omitempty"`
}

func NewMounter(s, t, mode string) (*Mounter, error) {
	sid, err := ParseID(s)
	if err != nil {
		return nil, err
	}

	tid, err := ParseID(t)
	if err != nil {
		return nil, err
	}

	return &Mounter{
		Source: sid,
		Target: tid,
		Mode:   mode,
		Status: common.ActiveStatus,
	}, nil
}

// Mount updates the target digivice's model with a mount reference to the source digivice;
// a mount is successful iff 1. source and target are compatible; 2. caller has sufficient
// access rights.
func (m *Mounter) Mount() error {
	client, err := config.NewK8sClient()
	if err != nil {
		return fmt.Errorf("unable to create k8s client: %v", err)
	}

	// source digivice
	_, err = GetResourceJson(client.DynamicClient, m.Source)
	if err != nil {
		return fmt.Errorf("%v", err)
	}

	// target digivice
	tj, err := GetResourceJson(client.DynamicClient, m.Target)
	if err != nil {
		return fmt.Errorf("%v", err)
	}
	//log.Printf("%s\n%s", sj, tj)

	doMount := func() error {
		log.Println("mount: do", m.Mode)

		// add the mount reference (Kind.SpacedName) to the target
		//path := strings.Join([]string{common.MountRefPrefix, m.Source.Kind.Name, m.Source.SpacedName()}, ".")
		pathPrefix := []string{common.MountRefPrefix, m.Source.Kind.Name, m.Source.SpacedName()}

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
		return client.UpdateFromJson(tj, m.Target.Namespace)
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
