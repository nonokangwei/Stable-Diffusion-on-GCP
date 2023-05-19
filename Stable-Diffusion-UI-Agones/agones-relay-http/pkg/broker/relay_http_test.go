package broker

import (
	v1 "agones.dev/agones/pkg/apis/agones/v1"
	"context"
	"github.com/Octops/agones-event-broadcaster/pkg/events"
	"github.com/Octops/agones-relay-http/internal/runtime"
	"github.com/stretchr/testify/require"
	"io/ioutil"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"net/http"
	"strings"
	"sync"
	"testing"
)

func TestRelayHTTP_SendMessage(t *testing.T) {
	gs := &v1.GameServer{
		ObjectMeta: metav1.ObjectMeta{
			UID:       "a3fb9d0c-7b1f-4fa3-892c-723a6ddf627b",
			Name:      "gameserver-udp",
			Namespace: "default",
			Labels: map[string]string{
				"region": "us-east-1",
			},
			ResourceVersion: "1000",
		},
		Status: v1.GameServerStatus{
			State:   "Ready",
			Address: "172.134.34.53:7654",
			Players: &v1.PlayerStatus{
				Count: 10,
			},
		},
	}

	testCases := []struct {
		name          string
		endpointURL   string
		requestMethod string
		envelope      *events.Envelope
		respBody      string
		wantURL       string
		wantErr       bool
	}{
		{
			name:          "it should send a message for OnAdd event",
			endpointURL:   "http://localhost:8090/add",
			requestMethod: http.MethodPost,
			envelope: &events.Envelope{
				Header: &events.Header{
					Headers: map[string]string{
						"event_source": events.EventSourceOnAdd.String(),
						"event_type":   events.GameServerEventAdded.String(),
					},
				},
				Message: events.GameServerAdded(&events.EventMessage{
					Body: gs,
				}),
			},
			respBody: "received OnAdd",
			wantURL:  "http://localhost:8090/add",
			wantErr:  false,
		},
		{
			name:          "it should send a message for OnUpdate event",
			endpointURL:   "http://localhost:8090/update",
			requestMethod: http.MethodPut,
			envelope: &events.Envelope{
				Header: &events.Header{
					Headers: map[string]string{
						"event_source": events.EventSourceOnUpdate.String(),
						"event_type":   events.GameServerEventUpdated.String(),
					},
				},
				Message: events.GameServerUpdated(&events.EventMessage{
					Body: gs,
				}),
			},
			respBody: "received OnUpdate",
			wantURL:  "http://localhost:8090/update",
			wantErr:  false,
		},
		{
			name:          "it should send a message for OnDelete event",
			endpointURL:   "http://localhost:8090/delete",
			requestMethod: http.MethodDelete,
			envelope: &events.Envelope{
				Header: &events.Header{
					Headers: map[string]string{
						"event_source": events.EventSourceOnDelete.String(),
						"event_type":   events.GameServerEventDeleted.String(),
					},
				},
				Message: events.GameServerDeleted(&events.EventMessage{
					Body: gs,
				}),
			},
			respBody: "received OnDelete",
			wantURL:  "http://localhost:8090/delete?event_type=gameserver.events.deleted&name=gameserver-udp&namespace=default",
			wantErr:  false,
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			logger := runtime.NewLogger(true)

			wg := sync.WaitGroup{}
			wg.Add(1)

			var response *http.Response
			client := func(req *http.Request) (*http.Response, error) {
				response = &http.Response{
					Status:  "200 OK",
					Body:    ioutil.NopCloser(strings.NewReader(tc.respBody)), //req.Body, //ioutil.NopCloser(strings.NewReader("OK")),
					Request: req,
				}
				wg.Done()
				return response, nil
			}

			relay, err := NewRelayHTTP(logger, RelayConfig{
				OnAddUrl:    "http://localhost:8090/add",
				OnUpdateUrl: "http://localhost:8090/update",
				OnDeleteUrl: "http://localhost:8090/delete",
			}, client)

			require.NoError(t, err)

			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()

			go relay.Start(ctx)

			err = relay.SendMessage(tc.envelope)
			require.NoError(t, err)

			wg.Wait()
			body, err := ioutil.ReadAll(response.Body)
			require.NoError(t, err)
			require.Equal(t, tc.respBody, string(body))
			require.Equal(t, tc.requestMethod, response.Request.Method)
			require.Equal(t, tc.wantURL, response.Request.URL.String())
		})
	}
}
