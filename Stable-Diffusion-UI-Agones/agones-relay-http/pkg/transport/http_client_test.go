package transport

import (
	"context"
	"errors"
	"fmt"
	"github.com/Octops/agones-relay-http/internal/runtime"
	"github.com/sirupsen/logrus"
	"github.com/stretchr/testify/require"
	"io"
	"io/ioutil"
	"log"
	"math/rand"
	"net/http"
	"strings"
	"testing"
	"time"
)

func TestNewClient(t *testing.T) {
	logger := runtime.NewLogger(true)

	type args struct {
		logger  *logrus.Entry
		timeout string
	}
	testCases := []struct {
		name       string
		args       args
		want       *Client
		wantErr    bool
		wantErrMsg string
	}{
		{
			name: "it should return a client with a 10s timeout",
			args: args{
				logger:  logger,
				timeout: "10s",
			},
			want: &Client{
				logger: logger,
				client: &http.Client{
					Timeout: time.Second * 10,
				},
			},
			wantErr: false,
		},
		{
			name: "it should return a client with a 1m timeout",
			args: args{
				logger:  logger,
				timeout: "1m",
			},
			want: &Client{
				logger: logger,
				client: &http.Client{
					Timeout: time.Minute,
				},
			},
			wantErr: false,
		},
		{
			name: "it should return error for invalid timeout",
			args: args{
				logger:  logger,
				timeout: "abc",
			},
			want: &Client{
				logger: logger,
				client: nil,
			},
			wantErr:    true,
			wantErrMsg: "time: invalid duration abc",
		},
		{
			name: "it should return error for invalid alphanumeric timeout",
			args: args{
				logger:  logger,
				timeout: "12ss",
			},
			want: &Client{
				logger: logger,
				client: nil,
			},
			wantErr:    true,
			wantErrMsg: "time: unknown unit ss in duration 12ss",
		},
		{
			name: "it should return error for numeric and missing unit timeout",
			args: args{
				logger:  logger,
				timeout: "10",
			},
			want: &Client{
				logger: logger,
				client: nil,
			},
			wantErr:    true,
			wantErrMsg: "time: missing unit in duration 10",
		},
		{
			name: "it should return error for empty timeout",
			args: args{
				logger:  logger,
				timeout: "",
			},
			want: &Client{
				logger: logger,
				client: nil,
			},
			wantErr:    true,
			wantErrMsg: "time: invalid duration ",
		},
	}
	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			got, err := NewClient(tc.args.logger, tc.args.timeout)
			require.Equal(t, err != nil, tc.wantErr)

			if tc.wantErr == true {
				require.EqualError(t, errors.New(tc.wantErrMsg), err.Error())
			} else {
				require.NotNil(t, got)
				require.NotNil(t, got.client)
				require.Equal(t, got.client.Timeout, tc.want.client.Timeout)
			}
		})
	}
}

func TestClient_Do(t *testing.T) {
	rand.Seed(time.Now().UnixNano())
	min := 8000
	max := 9000
	port := rand.Intn(max-min) + min

	type args struct {
		method string
		url    string
		body   io.Reader
	}
	testCases := []struct {
		name    string
		args    args
		want    *http.Response
		wantErr bool
	}{
		{
			name: "it should send POST to endpoint and return StatusCode 200 OK",
			args: args{
				method: http.MethodPost,
				url:    fmt.Sprintf("http://localhost:%d", port),
				body:   strings.NewReader("Payload POST"),
			},
			want: &http.Response{
				StatusCode: http.StatusOK,
			},
			wantErr: false,
		},
		{
			name: "it should send PUT to endpoint and return StatusCode 200 OK",
			args: args{
				method: http.MethodPut,
				url:    fmt.Sprintf("http://localhost:%d", port),
				body:   strings.NewReader("Payload PUT"),
			},
			want: &http.Response{
				StatusCode: http.StatusOK,
			},
			wantErr: false,
		},
		{
			name: "it should send DELETE to endpoint and return StatusCode 200 OK",
			args: args{
				method: http.MethodDelete,
				url:    fmt.Sprintf("http://localhost:%d", port),
				body:   strings.NewReader("Payload DELETE"),
			},
			want: &http.Response{
				StatusCode: http.StatusOK,
			},
			wantErr: false,
		},
		{
			name: "it should return error if endpoint is not available",
			args: args{
				method: http.MethodPost,
				url:    "http://localhost:10000",
				body:   strings.NewReader("Payload POST"),
			},
			want:    nil,
			wantErr: true,
		},
	}

	logger := runtime.NewLogger(true)
	ctx, cancel := context.WithCancel(context.Background())
	go startServer(ctx, fmt.Sprintf(":%d", port))

	defer cancel()

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			client, err := NewClient(logger, "10s")
			require.NotNil(t, client)
			require.NoError(t, err)

			req, err := http.NewRequest(tc.args.method, tc.args.url, tc.args.body)
			require.NoError(t, err)

			client.retries = 2
			client.interval = time.Second
			got, err := client.Do(req)
			require.Equal(t, err != nil, tc.wantErr)

			if tc.wantErr {
				require.Nil(t, got)
			} else {
				require.Equal(t, tc.want.StatusCode, got.StatusCode)
			}
		})
	}
}

func startServer(ctx context.Context, addr string) {
	server := &http.Server{Addr: addr}

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		body, err := ioutil.ReadAll(r.Body)
		if err != nil {
			log.Printf("Error reading body: %v", err)
			http.Error(w, "can't read body", http.StatusBadRequest)
			return
		}

		log.Printf("%s", body)
		fmt.Fprintf(w, "%s", body)
	})

	log.Println("server listening at", server.Addr)

	go func() {
		if err := server.ListenAndServe(); err != nil {
			panic(err)
		}
	}()

	<-ctx.Done()

	log.Println("stopping server")

	if err := server.Shutdown(ctx); err != nil {
		log.Print(err)
	}
}
