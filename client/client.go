package client

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/client-go/restmapper"

	"digi.dev/digivice/client/k8s"
	"digi.dev/digivice/pkg/core"
)


type Client struct {
	k *k8s.K8sClient
}

func NewClient() (*Client, error) {
	kc, err := k8s.NewClientSet()
	if err != nil {
		return nil, err
	}
	return &Client{
		k: kc,
	}, nil
}

func (c *Client) GetResourceJson(ar *core.Auri) (string, error) {
	gvr := ar.Gvr()
	d, err := c.k.DynamicClient.Resource(gvr).Namespace(ar.Namespace).Get(context.TODO(), ar.Name, metav1.GetOptions{})
	if err != nil {
		return "", fmt.Errorf("unable to get digivice %v: %v", gvr, err)
	}

	j, err := json.MarshalIndent(d, "", "  ")
	if err != nil {
		return "", fmt.Errorf("unable to parse digivice %s: %v", j, err)
	}

	return string(j), nil
}

// UpdateFromJson updates the API resource on the apiserver specified in the given json string.
// It uses the resource discovery and dynamic client to avoid unmarshalling into a concrete type.
func (c *Client) UpdateFromJson(j, namespace string) error {
	var obj *unstructured.Unstructured
	if err := json.Unmarshal([]byte(j), &obj); err != nil {
		return fmt.Errorf("unable to unmarshall %s: %v", j, err)
	}

	// update the target
	gvk := obj.GroupVersionKind()
	gk := schema.GroupKind{Group: gvk.Group, Kind: gvk.Kind}

	// XXX use controller-runtime's generic client to avoid the discovery? (see syncer)
	// TODO: measure time;
	groupResources, err := restmapper.GetAPIGroupResources(c.k.Clientset.Discovery())
	if err != nil {
		return fmt.Errorf("unable to discover resources: %v", err)
	}

	rm := restmapper.NewDiscoveryRESTMapper(groupResources)
	mapping, err := rm.RESTMapping(gk, gvk.Version)

	if err != nil {
		return fmt.Errorf("unable to map resource: %v", err)
	}

	_, err = c.k.DynamicClient.Resource(mapping.Resource).Namespace(namespace).Update(context.TODO(), obj, metav1.UpdateOptions{})
	return err
}

// ParseAuri returns an Auri from a slash separated string.
// The following string formats are allowed:
//  1. /group/ver/schema_name/namespace/name.[];
//  2. /group/ver/schema_name/name.[] (use default namespace);
//  3. /namespace/name.[];
//  4. /name.[] (use alias);
//  5. name.[] (use alias);
// .[]: model attributes
func ParseAuri(s string) (core.Auri, error) {
	ss := strings.Split(s, fmt.Sprintf("%c", core.UriSeparator))
	var g, v, kn, ns, n, path, other string
	switch len(ss) {
	case 6:
		g, v, kn, ns, other = ss[1], ss[2], ss[3], ss[4], ss[5]
	case 5:
		g, v, kn, ns, other = ss[1], ss[2], ss[3], core.DefaultNamespace, ss[4]
	case 3:
		return core.Auri{}, fmt.Errorf("unimplemented")
	case 2:
		auri, err := Resolve(ss[1])
		if err != nil {
			return core.Auri{}, err
		}
		return *auri, nil
	case 1:
		auri, err := Resolve(ss[0])
		if err != nil {
			return core.Auri{}, err
		}
		return *auri, nil
	default:
		return core.Auri{}, fmt.Errorf("auri needs to have either 5, 2, or 1 fields, "+
			"given %d in %s; each field starts with a '/' except for single "+
			"name on default namespace", len(ss)-1, s)
	}

	ss = strings.Split(other, fmt.Sprintf("%c", core.AttrPathSeparator))
	if len(ss) > 1 {
		n = ss[0]
		path = strings.Join(ss[1:], fmt.Sprintf("%c", core.AttrPathSeparator))
	} else {
		n = other
		path = ""
	}

	return core.Auri{
		Kind: core.Kind{
			Group:   g,
			Version: v,
			Name:    kn,
		},
		Namespace: ns,
		Name:      n,
		Path:      path,
	}, nil
}

// XXX add auri inference rules, e.g., if only the name is given, lookup local config for
// the auri string; use the auri string to access the model; if error, ask the user to
// provide the full auri