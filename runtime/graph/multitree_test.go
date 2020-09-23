package graph

import "testing"

func TestMultiTree(t *testing.T) {
	mt := &MultiTree{
		nodes: make(map[string]*node),
		trees: make(map[string]*tree),
	}
	nodes := []string{
		"A", "B", "U", "X", "V", "W", "Y", "Z",
	}
	edges := []struct {
		start string
		end   string
	}{
		{
			start: "A",
			end:   "U",
		},
		{
			start: "A",
			end:   "X",
		},
		{
			start: "U",
			end:   "V",
		},
		{
			start: "U",
			end:   "W",
		},
		{
			start: "X",
			end:   "Y",
		},
		{
			start: "X",
			end:   "Z",
		},
	}

	for _, n := range nodes {
		mt.AddNode(n)
	}

	for _, e := range edges {
		if err := mt.AddEdge(e.start, e.end); err != nil {
			t.Errorf("error adding edge %v:%v", e, err)
		}
	}

	t.Logf("current multi-tree:\n%s", mt.String())

	// make it a multi-tree
	edges = []struct {
		start string
		end   string
	}{
		{
			start: "B",
			end:   "V",
		},
		{
			start: "B",
			end:   "X",
		},
	}
	for _, e := range edges {
		if err := mt.AddEdge(e.start, e.end); err != nil {
			t.Errorf("error adding edge %v:%v", e, err)
		}
	}
	t.Logf("current multi-tree:\n%s", mt.String())

	// disallowed
	t.Logf("adding edge B-Z (should fail)..")
	err := mt.AddEdge("B", "Z")
	if err == nil {
		t.Errorf("call to AddEdge should fail")
	}
	t.Logf("call to AddEdge failed: %v", err)

	// disallowed
	t.Logf("adding edge B-U (should fail)..")
	err = mt.AddEdge("B", "U")
	if err == nil {
		t.Errorf("call to AddEdge should fail")
	}
	t.Logf("call to AddEdge failed: %v", err)

	// allowed
	t.Logf("adding edge B-W..")
	err = mt.AddEdge("B", "W")
	if err != nil {
		t.Errorf("error adding edge %v:%v", "B-W", err)
	}
	t.Logf("current multi-tree:\n%s", mt.String())

	// edge removal
	t.Logf("removing edge B-X..")
	err = mt.RemoveEdge("B", "X")
	if err != nil {
		t.Errorf("error removing edge %v:%v", "B-X", err)
	}
	t.Logf("current multi-tree:\n%s", mt.String())

	// node removal
	t.Logf("removing node A..")
	err = mt.RemoveNode("A")
	if err != nil {
		t.Errorf("error removing node %v:%v", "A", err)
	}
	t.Logf("current multi-tree:\n%s", mt.String())
}
