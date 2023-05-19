package broker

import (
	"encoding/json"
	"fmt"
	"github.com/Octops/agones-event-broadcaster/pkg/events"
	"github.com/pkg/errors"
	"io"
	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"net/http"
	"net/url"
	"strings"
)

type RelayRequest struct {
	Method    string
	Endpoints []string
	Payload   *Payload
}

type Payload struct {
	Body *events.Envelope `json:"body"`
}

type RequestQueue struct {
	Name  string
	Queue chan *RelayRequest
}

func (p *Payload) Read(b []byte) (n int, err error) {
	j, err := json.Marshal(p)
	if err != nil {
		return 0, errors.Wrap(io.ErrUnexpectedEOF, err.Error())
	}

	count := copy(b, j)
	return count, io.EOF
}

func createRequest(record *EventRelayRecord, envelope *events.Envelope) *RelayRequest {
	request := &RelayRequest{
		Method: record.Method,
	}

	switch record.Method {
	case http.MethodPost, http.MethodPut:
		request.Payload = &Payload{
			Body: envelope,
		}
		request.Endpoints = record.URL
	case http.MethodDelete:
		request.Endpoints = makeDeleteURLEndpoints(record.URL, envelope)
	}

	return request
}

func makeDeleteURLEndpoints(endpoints []string, envelope *events.Envelope) []string {
	deleteEndpoints := []string{}
	typeFromEnvelope := getEventTypeFromEnvelope(envelope)
	namespace, name := getResourceKeyFromMessage(envelope.Message.(events.Message))

	for _, ep := range endpoints {
		params := map[string]string{
			"event_type": strings.ToLower(typeFromEnvelope),
			"namespace":  namespace,
			"name":       name,
		}
		deleteEndpoints = append(deleteEndpoints, fmt.Sprintf("%s?%s", ep, encodeUrlParams(params)))
	}

	return deleteEndpoints
}

func encodeUrlParams(params map[string]string) string {
	values := url.Values{}
	for k, v := range params {
		values.Add(k, v)
	}

	return values.Encode()
}

func getEventTypeFromEnvelope(envelope *events.Envelope) string {
	if _, ok := envelope.Header.Headers["event_type"]; !ok {
		return "unknown"
	}

	return envelope.Header.Headers["event_type"]
}

func getResourceKeyFromMessage(msg events.Message) (string, string) {
	res := msg.Content().(v1.Object)

	namespace := res.GetNamespace()
	name := res.GetName()

	return namespace, name
}
