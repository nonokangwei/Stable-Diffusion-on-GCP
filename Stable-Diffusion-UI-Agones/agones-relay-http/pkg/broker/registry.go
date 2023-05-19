package broker

import "fmt"

type EventRelayRecord struct {
	Method       string
	URL          []string
	RequestQueue *RequestQueue
}

type EventRelayRegistry struct {
	Records map[string]*EventRelayRecord
}

func (r *EventRelayRegistry) Register(eventSource string, record *EventRelayRecord) {
	if len(r.Records) == 0 {
		r.Records = map[string]*EventRelayRecord{}
	}

	r.Records[eventSource] = record
}

func (r *EventRelayRegistry) Get(eventSource string) (*EventRelayRecord, error) {
	if _, ok := r.Records[eventSource]; !ok {
		return nil, fmt.Errorf("event %q is not registry, sending aborted", eventSource)
	}

	return r.Records[eventSource], nil
}
