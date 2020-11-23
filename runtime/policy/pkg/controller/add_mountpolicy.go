package controller

import (
	"digi.dev/digivice/runtime/policy/pkg/controller/mountpolicy"
)

func init() {
	// AddToManagerFuncs is a list of functions to create controllers and add them to a manager.
	AddToManagerFuncs = append(AddToManagerFuncs, mountpolicy.Add)
}
