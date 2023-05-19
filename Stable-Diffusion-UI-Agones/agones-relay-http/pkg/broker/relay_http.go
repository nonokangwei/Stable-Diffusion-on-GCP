package broker

import (
	"context"
	"fmt"
	"github.com/Octops/agones-event-broadcaster/pkg/events"
	"github.com/pkg/errors"
	"github.com/sirupsen/logrus"
	"net/http"
	"strings"
	"sync"
	"time"
)

type RelayConfig struct {
	OnAddUrl       string
	OnUpdateUrl    string
	OnDeleteUrl    string
	WorkerReplicas int
}

type RelayHTTP struct {
	logger         *logrus.Entry
	wg             *sync.WaitGroup
	Client         Client
	Registry       *EventRelayRegistry
	Workers        []*Worker
	workerReplicas int
}

// TODO: Validate if URLs are valid http endpoints.
type Client func(req *http.Request) (*http.Response, error)

// TODO: Implement auth mechanism: BasicAuth
func NewRelayHTTP(logger *logrus.Entry, config RelayConfig, client Client) (*RelayHTTP, error) {
	applyConfigDefaults(&config)

	relay := &RelayHTTP{
		logger:         logger,
		wg:             &sync.WaitGroup{},
		Client:         client,
		Registry:       &EventRelayRegistry{},
		Workers:        make([]*Worker, config.WorkerReplicas*3), // 3 Events: OnAdd, OnUpdate, OnDelete
		workerReplicas: config.WorkerReplicas,
	}

	relay.Registry.Register(events.EventSourceOnAdd.String(), &EventRelayRecord{
		Method: http.MethodPost,
		URL:    strings.Split(config.OnAddUrl, ","),
		RequestQueue: &RequestQueue{
			Name:  "OnAdd",
			Queue: make(chan *RelayRequest, 1024),
		},
	})

	relay.Registry.Register(events.EventSourceOnUpdate.String(), &EventRelayRecord{
		Method: http.MethodPut,
		URL:    strings.Split(config.OnUpdateUrl, ","),
		RequestQueue: &RequestQueue{
			Name:  "OnUpdate",
			Queue: make(chan *RelayRequest, 1024),
		},
	})

	relay.Registry.Register(events.EventSourceOnDelete.String(), &EventRelayRecord{
		Method: http.MethodDelete,
		URL:    strings.Split(config.OnDeleteUrl, ","),
		RequestQueue: &RequestQueue{
			Name:  "OnDelete",
			Queue: make(chan *RelayRequest, 1024),
		},
	})

	return relay, nil
}

func (r *RelayHTTP) Start(ctx context.Context) error {
	r.InitWorkers(r.workerReplicas, r.Client)
	if err := r.StartWorkers(ctx); err != nil {
		r.logger.Fatal(errors.Wrap(err, "workers could not be started"))
	}

	<-ctx.Done()
	r.logger.Info("stopping Relay HTTP broker")
	r.wg.Wait()

	return nil
}

func (r *RelayHTTP) InitWorkers(replicas int, client Client) {
	count := 0
	for _, record := range r.Registry.Records {
		rr := record
		for i := 0; i < replicas; i++ {
			id := i + 1
			workerID := fmt.Sprintf("%d", id)
			r.Workers[count] = NewWorker(workerID, rr.RequestQueue, client)
			count++
		}
	}
}

func (r *RelayHTTP) StartWorkers(ctx context.Context) error {
	for i := 0; i < len(r.Workers); i++ {
		r.wg.Add(1)
		i := i
		go func() {
			defer r.wg.Done()

			if err := r.Workers[i].Start(ctx); err != nil {
				r.logger.Fatal(errors.Wrap(err, "error starting worker"))
			}
		}()
	}

	return nil
}

// Called by the Broadcaster and builds the envelope that will be send as argument to the SendMessage function
func (r *RelayHTTP) BuildEnvelope(event events.Event) (*events.Envelope, error) {
	envelope := &events.Envelope{}

	envelope.AddHeader("event_source", event.EventSource().String())
	envelope.AddHeader("event_type", event.EventType().String())
	envelope.Message = event.(events.Message)

	return envelope, nil
}

// Called by the Broadcaster when a new event happens
func (r *RelayHTTP) SendMessage(envelope *events.Envelope) error {
	eventSource, err := getEventSourceHeader(envelope)
	if err != nil {
		return err
	}

	record, err := r.Registry.Get(eventSource)
	if err != nil {
		return errors.Wrap(err, "aborting sending message")
	}

	return r.EnqueueRequest(record.RequestQueue.Queue, createRequest(record, envelope))
}

func (r *RelayHTTP) EnqueueRequest(queue chan *RelayRequest, request *RelayRequest) error {
	select {
	case queue <- request:
	case <-time.After(5 * time.Second):
		return errors.New("request could not be enqueued due to timeout")
	}

	return nil
}

func applyConfigDefaults(config *RelayConfig) {
	if config.WorkerReplicas <= 0 {
		config.WorkerReplicas = 1
	}
}

func getEventSourceHeader(envelope *events.Envelope) (string, error) {
	if _, ok := envelope.Header.Headers["event_source"]; !ok {
		return "", errors.New("envelope header does not contain a valid event_source")
	}

	eventSource := envelope.Header.Headers["event_source"]
	return eventSource, nil
}
