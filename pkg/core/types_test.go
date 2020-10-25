package core

import (
	"encoding/json"
	"testing"
)

func TestMountRef(t *testing.T) {
	m := MountRef{
		Status: "expose",
		Mode:   "active",
	}
	ms, err := json.Marshal(m)
	if err != nil {
		t.Logf("unable to marshal: %v", err)
	}
	t.Logf("%s", string(ms))
}
