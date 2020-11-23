package yieldpolicy

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"sync"

	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller"
	"sigs.k8s.io/controller-runtime/pkg/handler"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
	"sigs.k8s.io/controller-runtime/pkg/source"

	"github.com/itchyny/gojq"

	"digi.dev/digivice/pkg/core"
	"digi.dev/digivice/pkg/helper"
	digiv1 "digi.dev/digivice/runtime/policy/pkg/apis/digi/v1"
)

const (
	name       = "yieldpolicy_controller"
	policyTag  = "policy"
	enforceTag = "enforce"

	ACTIVE   = core.MountActiveStatus
	INACTIVE = core.MountActiveStatus
)

var (
	this controller.Controller
)

type Policy struct {
	name string
	digiv1.YieldPolicySpec
}

type Policies map[string]*Policy

// TBD make a generic binding cache with dynamic watches
type PolicyCache struct {
	policies Policies

	modelToPolicies map[string]Policies

	// kinds that have been watched
	watched map[string]struct{}

	// apiserver client
	client client.Client

	mu sync.RWMutex
}

func (pc *PolicyCache) Add(p *Policy) error {
	pc.mu.Lock()
	defer pc.mu.Unlock()

	pc.policies[p.name] = p

	var srcKind, targetKind string

	// add watches
	// XXX add label selector predicate
	addWatchFunc := func(auri *core.Auri) error {
		o, err := getObj(pc.client, *auri)
		if err != nil {
			return err
		}

		return this.Watch(&source.Kind{
			Type: o,
		}, &handler.EnqueueRequestsFromMapFunc{
			ToRequests: helper.MuxRequest(enforceTag),
		})
	}

	srcKind = p.Source.Kind.String()
	if _, ok := pc.watched[srcKind]; !ok {
		if err := addWatchFunc(&p.Source); err != nil {
			log.Println(err)
			return err
		}
		pc.watched[srcKind] = struct{}{}
	}

	targetKind = p.Target.Kind.String()
	if _, ok := pc.watched[targetKind]; !ok {
		if err := addWatchFunc(&p.Target); err != nil {
			log.Println(err)
			return err
		}
		pc.watched[targetKind] = struct{}{}
	}

	// update model to policy lookup
	srcName, targetName := p.Source.SpacedName().String(), p.Target.SpacedName().String()

	setFunc := func(m map[string]Policies, k1, k2 string, v *Policy) {
		_, ok := m[k1]
		if !ok {
			m[k1] = make(Policies)
		}
		m[k1][k2] = v
	}

	m := pc.modelToPolicies
	setFunc(m, srcName, p.name, p)
	setFunc(m, targetName, p.name, p)
	return nil
}

func (pc *PolicyCache) Remove(name string) {
	pc.mu.Lock()
	defer pc.mu.Unlock()

	pl, ok := pc.policies[name]
	if !ok {
		return
	}
	delete(pc.policies, name)

	var srcName, targetName string
	srcName = pl.Source.SpacedName().String()
	targetName = pl.Target.SpacedName().String()

	srcPls, ok := pc.modelToPolicies[srcName]
	if ok {
		delete(srcPls, name)
	}

	targetPls, ok := pc.modelToPolicies[targetName]
	if ok {
		delete(targetPls, name)
	}
}

type ReconcileYieldPolicy struct {
	client      client.Client
	scheme      *runtime.Scheme
	policyCache *PolicyCache
}

func Add(mgr manager.Manager) error {
	r := newReconciler(mgr)

	c, err := controller.New(name, mgr, controller.Options{Reconciler: r})
	if err != nil {
		return err
	}

	this = c

	if err = c.Watch(&source.Kind{
		Type: &digiv1.YieldPolicy{},
	}, &handler.EnqueueRequestsFromMapFunc{
		ToRequests: helper.MuxRequest(policyTag),
	}); err != nil {
		return nil
	}

	return nil
}

// newReconciler returns a new reconcile.Reconciler
func newReconciler(mgr manager.Manager) reconcile.Reconciler {
	c := mgr.GetClient()
	return &ReconcileYieldPolicy{
		client: c,
		scheme: mgr.GetScheme(),
		policyCache: &PolicyCache{
			policies:        make(map[string]*Policy),
			modelToPolicies: make(map[string]Policies),
			watched:         make(map[string]struct{}),
			client:          c,
		},
	}
}

func (r *ReconcileYieldPolicy) Reconcile(request reconcile.Request) (reconcile.Result, error) {
	log.Println("Reconciling YieldPolicy")

	request, tag := helper.DemuxRequest(request)

	switch tag {
	case policyTag:
		return r.doPolicy(request)
	case enforceTag:
		// XXX need better event filter to avoid excessive invocation
		return r.doEnforce(request)
	}

	return reconcile.Result{}, nil
}

func (r *ReconcileYieldPolicy) doPolicy(request reconcile.Request) (reconcile.Result, error) {
	log.Println("do YieldPolicy")

	var name string
	name = request.String()

	yp := &digiv1.YieldPolicy{}
	err := r.client.Get(context.TODO(), request.NamespacedName, yp)

	if err != nil {
		if errors.IsNotFound(err) {
			r.policyCache.Remove(name)
			return reconcile.Result{}, nil
		}
		return reconcile.Result{}, err
	}

	log.Printf("handle policy %s: %v", name, yp.Spec)

	if err := r.policyCache.Add(&Policy{
		name:            name,
		YieldPolicySpec: yp.Spec,
	});
		err != nil {
		return reconcile.Result{}, err
	}

	// TBD does not seem to matter whether the source or the target is enqueued
	return r.doEnforce(reconcile.Request{
		NamespacedName: yp.Spec.Source.SpacedName(),
	})
}

func (r *ReconcileYieldPolicy) doEnforce(request reconcile.Request) (reconcile.Result, error) {
	var pls Policies
	pls, ok := r.policyCache.modelToPolicies[request.String()]
	if !ok {
		return reconcile.Result{}, nil
	}

	log.Println("do Enforce")

	// iterate and enforce all policies related to this model, as source or as target
	var err error
	for _, pl := range pls {
		log.Println("enforcing policy:", pl)
		var plSrc, plTarget *unstructured.Unstructured

		plSrc, err = getObj(r.client, pl.Source)

		// XXX log to sync reasons
		if err != nil {
			log.Println("unable to get source model:", pl.Source)
			continue
		}

		plTarget, err = getObj(r.client, pl.Target)
		if err != nil {
			log.Println("unable to get target model:", pl.Target)
			continue
		}

		log.Println(plSrc.GetName(), plTarget.GetName())
		log.Println("before:", plSrc, plTarget)

		// check if condition is met; the condition is written in jq;
		// it can take either or both the source and target models as
		// the inputs

		// parse the jq query
		query, err := gojq.Parse(pl.Condition)
		if err != nil {
			log.Fatalln(err)
		}

		iter := query.Run(map[string]interface{}{"source": plSrc.Object, "target": plTarget.Object})

		result, ok := iter.Next()
		if !ok {
			log.Println("queried but nil result:", ok)
			continue
		}

		// whether condition is met
		fired, ok := result.(bool)
		if !ok {
			log.Println("queried but unable to parse:", ok)
		}
		if !fired {
			continue
		}

		// update mounts; obtain the current mounts of the source and the target
		srcMounts, err := getMounts(plSrc)
		if err != nil {
			log.Println("err getting mounts:", plSrc.GetName(), err)
			return reconcile.Result{}, err
		}

		targetMounts, err := getMounts(plTarget)
		if err != nil {
			log.Println("err getting mounts:", plTarget.GetName(), err)
			return reconcile.Result{}, err
		}

		// any models mounted to both the source and the target AND are
		// active mounts to the source should now become active mounts
		// to the target
		log.Println(srcMounts, targetMounts)

		var updated bool
		for k, srcMtRefs := range srcMounts {
			targetMtRefs, ok := targetMounts[k]
			log.Println("CUR -> ", k, srcMtRefs)
			if !ok {
				continue
			}
			for n, srcMtRef := range srcMtRefs {
				targetMtRef, ok := targetMtRefs[n]
				if ok && srcMtRef.Status == ACTIVE {
					srcMtRef.Status = INACTIVE
					targetMtRef.Status = ACTIVE

					updated = true
				}
			}
		}

		if updated {
			plSrc, err = setMounts(plSrc, srcMounts)
			if err != nil {
				log.Println("err updating source's mounts", err)
				continue
			}

			plTarget, err = setMounts(plTarget, srcMounts)
			if err != nil {
				log.Println("err updating target's mounts", err)
				continue
			}
		}

		log.Println("after:", plSrc, plTarget)
		if err := r.client.Update(context.TODO(), plSrc); err != nil {
			log.Println("err updating source")
			continue
		}
		if err := r.client.Update(context.TODO(), plTarget); err != nil {
			log.Println("err updating target")
			// XXX better error handling
		}
	}

	return reconcile.Result{}, nil
}

// XXX move below to core helpers
func getMounts(o *unstructured.Unstructured) (map[string]core.MountRefs, error) {
	rawMounts, ok, err := unstructured.NestedMap(o.Object, core.MountAttrPathSlice...)
	if err != nil {
		return nil, err
	}
	if !ok {
		return nil, nil
	}

	var mounts map[string]core.MountRefs
	mounts = make(map[string]core.MountRefs)

	for n, m := range rawMounts {
		jsonBody, err := json.Marshal(m)
		if err != nil {
			return nil, fmt.Errorf("error marshalling mount references: %v", err)
		}

		var mr core.MountRefs
		if err := json.Unmarshal(jsonBody, &mr); err != nil {
			return nil, fmt.Errorf("error unmarshalling mount references: %v", err)
		}
		mounts[n] = mr
	}

	return mounts, nil
}

func setMounts(o *unstructured.Unstructured, mts map[string]core.MountRefs) (*unstructured.Unstructured, error) {
	jsonBody, err := json.Marshal(mts)
	if err != nil {
		return nil, err
	}

	var unstructuredMts map[string]interface{}
	if err := json.Unmarshal(jsonBody, &unstructuredMts); err != nil {
		return nil, err
	}

	log.Println("cur before ->", o.Object)
	err = unstructured.SetNestedMap(o.Object, unstructuredMts, core.MountAttrPathSlice...)
	if err != nil {
		return nil, err
	}
	log.Println("cur after ->", o.Object)
	return o, nil
}

func getObj(c client.Client, ar core.Auri) (*unstructured.Unstructured, error) {
	obj := &unstructured.Unstructured{}
	obj.SetGroupVersionKind(ar.Gvk())

	if err := c.Get(context.TODO(), ar.SpacedName(), obj); err != nil {
		return nil, err
	}
	return obj, nil
}
