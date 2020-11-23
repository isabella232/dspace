package mountpolicy

import (
	"log"

	"k8s.io/apimachinery/pkg/runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller"
	"sigs.k8s.io/controller-runtime/pkg/handler"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
	"sigs.k8s.io/controller-runtime/pkg/source"

	"digi.dev/digivice/pkg/helper"
	digiv1 "digi.dev/digivice/runtime/policy/pkg/apis/digi/v1"
)

const (
	name = "mountpolicy_controller"
)

type ReconcileMountPolicy struct {
	// This client, initialized using mgr.Client() above, is a split client
	// that reads objects from the cache and writes to the apiserver
	client client.Client
	scheme *runtime.Scheme
}

func Add(mgr manager.Manager) error {
	// Create a new reconciler
	r := newReconciler(mgr)

	// Create a new controller
	c, err := controller.New(name, mgr, controller.Options{Reconciler: r})
	if err != nil {
		return err
	}

	// Watch for changes to primary resource Sync
	if err = c.Watch(&source.Kind{
		Type: &digiv1.MountPolicy{},
	}, &handler.EnqueueRequestsFromMapFunc{
		ToRequests: helper.MuxRequest(""),
	}); err != nil {
		return err
	}

	return nil
}

// newReconciler returns a new reconcile.Reconciler
func newReconciler(mgr manager.Manager) reconcile.Reconciler {
	c := mgr.GetClient()
	return &ReconcileMountPolicy{
		client: c,
		scheme: mgr.GetScheme(),
	}
}

// TBD
func (r *ReconcileMountPolicy) Reconcile(request reconcile.Request) (reconcile.Result, error) {
	log.Println("Reconciling Sync")

	//_, _ := helper.DemuxRequest(request)

	return reconcile.Result{}, nil
}
