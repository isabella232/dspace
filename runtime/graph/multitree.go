package graph

import (
	"fmt"
	"log"

	"github.com/xlab/treeprint"
)

type stringSet map[string]struct{}

type node struct {
	value    string
	children map[string]*node
	roots    stringSet
}

type tree struct {
	root *node
}

type MultiTree struct {
	nodes map[string]*node
	trees map[string]*tree
}

func (ss stringSet) slice() []string {
	keys := make([]string, len(ss))

	i := 0
	for k := range ss {
		keys[i] = k
		i++
	}
	return keys
}

func buildPrintTree(n *node, pn treeprint.Tree) {
	cpn := pn.AddBranch(n.value)
	for _, cn := range n.children {
		buildPrintTree(cn, cpn)
	}
}

func (t *tree) String() string {
	pt := treeprint.New()
	buildPrintTree(t.root, pt)
	return pt.String()
}

func (mt *MultiTree) String() string {
	var s string
	for _, t := range mt.trees {
		s += t.String()
		s += "\n"
	}
	return s
}

func (mt *MultiTree) AddEdge(start, end string) error {
	sn, ok := mt.nodes[start]
	if !ok {
		return fmt.Errorf("start node %s does not exist", start)
	}

	en, ok := mt.nodes[end]
	if !ok {
		return fmt.Errorf("end node %s does not exist", end)
	}

	if _, ok := sn.children[end]; ok {
		log.Printf("edge exists: %s-%s", start, end)
		return nil
	}

	// check tree memberships for end and end's descendants
	if err := deepCompareRoots(en, sn.roots); err != nil {
		return err
	}

	// add the edge
	sn.children[end] = en

	// remove tree rooted at end
	delete(mt.trees, end)

	// remove end and add start's trees on
	// end's and its descendant' trees
	deepUpdateRoots([]string{end}, sn.roots.slice(), en)

	return nil
}

func deepUpdateRoots(rootsToDel, rootsToAdd []string, n *node) {
	for _, r := range rootsToDel {
		delete(n.roots, r)
	}

	for _, r := range rootsToAdd {
		n.roots[r] = struct{}{}
	}

	for _, cn := range n.children {
		deepUpdateRoots(rootsToDel, rootsToAdd, cn)
	}
}

func deepCompareRoots(n *node, roots stringSet) error {
	if r := intersect(n.roots, roots); r != "" {
		return fmt.Errorf("found node %s share root %v", n.value, r)
	}

	for _, cn := range n.children {
		if err := deepCompareRoots(cn, roots); err != nil {
			return err
		}
	}
	return nil
}

func intersect(rs1, rs2 stringSet) string {
	for k := range rs1 {
		if _, ok := rs2[k]; ok {
			return k
		}
	}
	return ""
}

func (mt *MultiTree) AddNode(n string) {
	if _, ok := mt.nodes[n]; ok {
		log.Printf("node %s exists", n)
		return
	}

	nn := &node{
		value:    n,
		children: make(map[string]*node),
		roots: stringSet{
			n: struct{}{},
		},
	}
	mt.nodes[n] = nn
	mt.trees[n] = &tree{
		root: nn,
	}
}

func (mt *MultiTree) DeleteEdge(start, end string) error {
	sn, ok := mt.nodes[start]
	if !ok {
		return fmt.Errorf("start node %s does not exist", start)
	}

	en, ok := mt.nodes[end]
	if !ok {
		return fmt.Errorf("end node %s does not exist", end)
	}

	if _, ok := sn.children[end]; !ok {
		return fmt.Errorf("edge does not exist: %s-%s", start, end)
	}

	delete(sn.children, end)

	for r := range sn.roots {
		delete(en.roots, r)
	}

	var newRoots []string
	if len(en.roots) == 0 {
		t := &tree{
			root: en,
		}
		mt.trees[end] = t
		newRoots = []string{end}
	}

	deepUpdateRoots(sn.roots.slice(), newRoots, en)

	return nil
}

func (mt *MultiTree) DeleteNode(name string) error {
	n, ok := mt.nodes[name]
	if !ok {
		return fmt.Errorf("%s does not exist", name)
	}

	for _, cn := range n.children {
		if err := mt.DeleteEdge(n.value, cn.value); err != nil {
			return err
		}
	}

	// TBD: alternatively, lookup via trees
	for _, n := range mt.nodes {
		delete(n.children, name)
	}

	delete(mt.nodes, name)
	return nil
}
