package core

import (
	"fmt"

	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/apimachinery/pkg/types"
	"strings"
)

const (
	Separator    = types.Separator
	SubSeparator = '.'
)

type MountRef struct {
	Mode   string `json:"mode,omitempty"`
	Status string `json:"status,omitempty"`
}

type PipeRef struct {
	Mode string `json:"mode,omitempty"`
}

// Kind identifies a model schema, e.g., digi.dev/v1/Lamp; it is a re-declaration of
// https://godoc.org/k8s.io/apimachinery/pkg/runtime/schema#GroupVersionResource with json tags and field name changes.
type Kind struct {
	// Model schema group
	Group string `json:"group,omitempty"`
	// Schema version
	Version string `json:"version,omitempty"`
	// Schema name; first letter capitalized, e.g., Roomba
	Name string `json:"name,omitempty"`
}

// Auri identifies a set of attributes belonging to a model on the semantic message bus
// E.g., /digi.dev/v1/Roomba/default/roomba-foo.power
type Auri struct {
	// model schema
	Kind Kind `json:"kind,omitempty"`
	// name of the model
	Name string `json:"name,omitempty"`
	// namespace of the model
	Namespace string `json:"namespace,omitempty"`
	// path to attribute(s) in the model; if path empty, Auri points to the model
	Path string `json:"path,omitempty"`
}

func (k *Kind) Plural() string {
	// XXX allow reading plural from input or define a conversion rule
	return strings.ToLower(k.Name) + "s"
}

func (k *Kind) Gvr() schema.GroupVersionResource {
	return schema.GroupVersionResource{
		Group:    k.Group,
		Version:  k.Version,
		Resource: k.Plural(),
	}
}

func (k *Kind) String() string {
	return k.Gvr().String()
}

func (ar *Auri) Gvr() schema.GroupVersionResource {
	return ar.Kind.Gvr()
}

func (ar *Auri) Gvk() schema.GroupVersionKind {
	return schema.GroupVersionKind{
		Group:   ar.Kind.Group,
		Version: ar.Kind.Version,
		Kind:    ar.Kind.Name,
	}
}

func (ar *Auri) SpacedName() types.NamespacedName {
	return types.NamespacedName{
		Name:      ar.Name,
		Namespace: ar.Namespace,
	}
}

func (ar *Auri) String() string {
	if ar.Path == "" {
		return fmt.Sprintf("%s%c%s", ar.Gvr().String(), Separator, ar.SpacedName().String())
	}
	return fmt.Sprintf("%s%c%s%c%s", ar.Gvr().String(), Separator, ar.SpacedName().String(), SubSeparator, ar.Path)
}

// ParseAuri returns an Auri from a slash separated string.
// The following string formats are allowed:
//  1. /group/ver/schema_name/namespace/name;
//  2. /group/ver/schema_name/name (use default namespace);
//  3. /namespace/name;
//  4. /name (use default namespace);
//  5. name (use default namespace);
// XXX: parse dot for attribute
func ParseAuri(s string) (Auri, error) {
	ss := strings.Split(s, fmt.Sprintf("%c", Separator))
	var g, v, kn, ns, n string
	switch len(ss) {
	case 6:
		g, v, kn, ns, n = ss[1], ss[2], ss[3], ss[4], ss[5]
	case 5:
		g, v, kn, ns, n = ss[1], ss[2], ss[3], DefaultNamespace, ss[4]
	case 3:
		return Auri{}, fmt.Errorf("unimplemented")
	case 2:
		return Auri{}, fmt.Errorf("unimplemented")
	case 1:
		return Auri{}, fmt.Errorf("unimplemented")
	default:
		return Auri{}, fmt.Errorf("auri needs to have either 5, 2, or 1 fields, "+
			"given %d in %s; each field starts with a '/' except for single "+
			"name on default namespace", len(ss)-1, s)
	}
	return Auri{
		Kind: Kind{
			Group:   g,
			Version: v,
			Name:    kn,
		},
		Namespace: ns,
		Name:      n,
	}, nil
}
