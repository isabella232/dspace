package client

import (
	"encoding/json"
	"fmt"
	"log"
	"strings"

	"digi.dev/digivice/client/config"
	"github.com/tidwall/sjson"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/client-go/dynamic"
)

const (
	MountRefPrefix = "mounts"
	HideMode    = "hide"
	ExposeMode  = "expose"
	DefaultMode = ExposeMode
	DefaultNamespace = "default"
)

// Kind identifies a digivice model schema, e.g., digi.dev/v1/lamps
type Kind struct {
	// Model schema group
	Group string `json:"group"`
	// Schema version
	Version string `json:"version"`
	// Schema name in plural and non-capitalized, e.g., Lamp -> lamps
	Name string `json:"string"`
}

// ID identifies a digivice model, e.g., digi.dev/v1/lamps/default/lamp-1
type ID struct {
	Kind      *Kind  `json:"kind"`
	Name      string `json:"name"`
	Namespace string `json:"namespace"`
}

// Mounter contains methods to perform a mount
type Mounter struct {
	Source *ID    `json:"source"`
	Target *ID    `json:"target"`
	Mode   string `json:"mode"`
}

func (k *Kind) Gvr() schema.GroupVersionResource {
	return schema.GroupVersionResource{
		Group:    k.Group,
		Version:  k.Version,
		Resource: k.Name,
	}
}

func (k *Kind) String() string {
	return strings.Join([]string{k.Group, k.Version, k.Name}, "/")
}

func (i *ID) SpacedName() string{
	return strings.Join([]string{i.Namespace, i.Name}, "/")
}

// ParseID returns a parsed digivice ID from a slash separated string.
// The following string formats are allowed:
//  1. /group/ver/schema_name/namespace/name;
//  2. /group/ver/schema_name/name (use default namespace);
//  3. /namespace/name;
//  4. /name (use default namespace);
//  5. name (use default namespace);
// For 3-5, Mounter will fetch the spacedNames to kinds mapping.
func ParseID(s string) (*ID, error) {
	ss := strings.Split(s, "/")
	var g, v, kn, ns, n string
	switch len(ss) {
	case 6:
		g, v, kn, ns, n = ss[1], ss[2], ss[3], ss[4], ss[5]
	case 5:
		g, v, kn, ns, n = ss[1], ss[2], ss[3], DefaultNamespace, ss[4]
	case 3:
		return nil, fmt.Errorf("unimplemented")
	case 2:
		return nil, fmt.Errorf("unimplemented")
	case 1:
		return nil, fmt.Errorf("unimplemented")
	default:
		return nil, fmt.Errorf("id needs to have either 5, 2, or 1 fields, "+
			"given %d in %s; each field starts with a '/' except for single "+
			"name on default namespace", len(ss)-1, s)
	}
	return &ID{
		Kind: &Kind{
			Group:   g,
			Version: v,
			Name:    kn,
		},
		Namespace: ns,
		Name:      n,
	}, nil
}

func (i *ID) String() string {
	return strings.Join([]string{i.Kind.String(), i.Namespace, i.Name}, "/")
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
	_, err = getDigiviceJson(client.DynamicClient, m.Source)
	if err != nil {
		return fmt.Errorf("%v", err)
	}

	// target digivice
	tj, err := getDigiviceJson(client.DynamicClient, m.Target)
	if err != nil {
		return fmt.Errorf("%v", err)
	}
	//log.Printf("%s\n%s", sj, tj)
	// TODO:
	// 1. compatibility check - whether src can be added to target's mount reference;
	// 2. access right check - whether the caller has sufficient access rights to do writes;
	// 3. mount rule check - whether the mount breaks the mount rule;
	// 4. yield policy check - whether the mount has yield flag set if there is an active mount already;
	// 5. nits: whether the digivice has been mounted etc.

	// expose
	doExpose := func() error {
		log.Println("mount: do expose")

		// add the mount reference (Kind.SpacedName) to the target
		path := strings.Join([]string{MountRefPrefix, m.Source.Kind.Name, m.Source.SpacedName()}, ".")

		tj, err := sjson.SetRaw(tj, path, "\"" + ExposeMode + "\"")
		if err != nil {
			return fmt.Errorf("unable to merge json: %v", err)
		}

		// update the target
		return client.UpdateFromJson(tj, m.Target.Namespace)
	}

	// hide
	doHide := func() error {
		log.Println("mount: do hide")
		log.Fatalf("TODO: unimplemented")
		return nil
	}

	switch m.Mode {
	case ExposeMode:
		return doExpose()
	case HideMode:
		return doHide()
	default:
		return nil
	}
}

func (m *Mounter) Unmount() error {
	// TODO
	return nil
}

func (m *Mounter) Yield() error {
	// TODO
	return nil
}

func getDigiviceJson(client dynamic.Interface, i *ID) (string, error) {
	gvr := i.Kind.Gvr()
	d, err := client.Resource(gvr).Namespace(i.Namespace).Get(i.Name, metav1.GetOptions{})
	if err != nil {
		return "", fmt.Errorf("unable to get digivice %v: %v", gvr, err)
	}

	j, err := json.MarshalIndent(d, "", "  ")
	if err != nil {
		return "", fmt.Errorf("unable to parse digivice %s: %v", j, err)
	}

	return string(j), nil
}
