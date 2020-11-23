package v1

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	"digi.dev/digivice/pkg/core"
)

// MountPolicySpec defines the mount policies.
type MountPolicySpec struct {
	Source    core.Auri `json:"source,omitempty"`
	Target    core.Auri `json:"target,omitempty"`
	Condition string    `json:"condition,omitempty"`
	Action    string    `json:"action,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// MountPolicy is the Schema for the mountpolicies API
// +kubebuilder:resource:path=mountpolicies,scope=Namespaced
type MountPolicy struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec MountPolicySpec `json:"spec,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// MountPolicyList contains a list of MountPolicy
type MountPolicyList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []MountPolicy `json:"items"`
}

func init() {
	SchemeBuilder.Register(&MountPolicy{}, &MountPolicyList{})
}
