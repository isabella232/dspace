package config

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/client-go/dynamic"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/restmapper"
	"k8s.io/client-go/tools/clientcmd"
)

type K8sClient struct {
	Kubeconfig    *rest.Config
	DynamicClient dynamic.Interface
	Clientset     *kubernetes.Clientset
}

// UpdateFromJson update the API resource on the apiserver specified in the given json string.
// It uses the resource discovery and dynamic client to avoid unmarshalling into a concrete type.
func (k *K8sClient) UpdateFromJson(j, namespace string) error {
	var obj *unstructured.Unstructured
	if err := json.Unmarshal([]byte(j), &obj); err != nil {
		return fmt.Errorf("unable to unmarshall target: %v", err)
	}

	// update the target
	gvk := obj.GroupVersionKind()
	gk := schema.GroupKind{Group: gvk.Group, Kind: gvk.Kind}

	groupResources, err := restmapper.GetAPIGroupResources(k.Clientset.Discovery())
	if err != nil {
		return fmt.Errorf("unable to discover resources: %v", err)
	}

	rm := restmapper.NewDiscoveryRESTMapper(groupResources)
	mapping, err := rm.RESTMapping(gk, gvk.Version)

	if err != nil {
		return fmt.Errorf("unable to map resource: %v", err)
	}

	_, err = k.DynamicClient.Resource(mapping.Resource).Namespace(namespace).Update(obj, metav1.UpdateOptions{})
	return err
}

func NewK8sClient() (*K8sClient, error) {
	var kubeconfig *string
	if home := homeDir(); home != "" {
		kubeconfig = flag.String("kubeconfig", filepath.Join(home, ".kube", "config"), "(optional) absolute path to the kubeconfig file")
	} else {
		kubeconfig = flag.String("kubeconfig", "", "absolute path to the kubeconfig file")
	}
	flag.Parse()

	// use the current context in kubeconfig
	config, err := clientcmd.BuildConfigFromFlags("", *kubeconfig)
	if err != nil {
		return nil, err
	}

	// create dynamic client
	dc, err := dynamic.NewForConfig(config)
	if err != nil {
		return nil, err
	}

	// create the clientsetrn
	cs, err := kubernetes.NewForConfig(config)
	if err != nil {
		return nil, err
	}

	return &K8sClient{
		Kubeconfig:    config,
		DynamicClient: dc,
		Clientset:     cs,
	}, nil
}

func homeDir() string {
	if h := os.Getenv("HOME"); h != "" {
		return h
	}

	return os.Getenv("USERPROFILE") // windows
}
