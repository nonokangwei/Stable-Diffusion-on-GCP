package broker

import (
	"context"
	"github.com/Octops/agones-relay-http/internal/runtime"
	"github.com/pkg/errors"
	"github.com/sirupsen/logrus"
	"net/http"
	"strings"
)

type Worker struct {
	Id           string
	logger       *logrus.Entry
	RequestQueue *RequestQueue
	Client       Client
}

func NewWorker(id string, queue *RequestQueue, client Client) *Worker {
	return &Worker{
		logger: runtime.Logger().WithFields(logrus.Fields{
			"worker": id,
			"queue":  queue.Name,
		}),
		Id:           id,
		RequestQueue: queue,
		Client:       client,
	}
}

func (w *Worker) Start(ctx context.Context) error {
	w.logger.Info("starting worker")

	for {
		select {
		case request := <-w.RequestQueue.Queue:
			w.Do(request)
		case <-ctx.Done():
			w.logger.Info("stopping worker")
			return nil
		}
	}
}

func (w Worker) Do(request *RelayRequest) {
	for idx, _ := range request.Endpoints {
		url := strings.TrimSpace(request.Endpoints[idx])
		req, err := http.NewRequest(request.Method, url, request.Payload)

		response, err := w.Client(req)
		if err != nil {
			w.logger.Error(errors.Wrapf(err, "%s %s failed", request.Method, url))
			return
		}

		w.logger.Debugf("%s %s - %s", request.Method, url, response.Status)
	}
}
