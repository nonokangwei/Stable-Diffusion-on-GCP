package transport

import (
	"github.com/Octops/agones-relay-http/internal/runtime"
	"github.com/sirupsen/logrus"
	"net/http"
	"time"
)

type Client struct {
	logger   *logrus.Entry
	client   *http.Client
	retries  int
	interval time.Duration
}

func NewClient(logger *logrus.Entry, timeout string) (*Client, error) {
	duration, err := time.ParseDuration(timeout)
	if err != nil {
		return nil, err
	}

	return &Client{
		logger: logger,
		client: &http.Client{
			Timeout: duration,
		},
		retries:  5,
		interval: 5 * time.Second,
	}, nil
}

func (c *Client) Do(req *http.Request) (*http.Response, error) {
	req.Header.Set("Content-Type", "application/json")
	response := &http.Response{}
	fn := func(attempt, retries int) error {
		resp, err := c.client.Do(req)
		if err != nil {
			runtime.Logger().WithField("source", "client").Errorf("(%d/%d) %s %s failed", attempt, retries, req.Method, req.URL)
			return err
		}

		defer resp.Body.Close()
		response = resp
		return nil
	}

	err := withRetry(c.retries, c.interval, fn)
	if err != nil {
		return nil, err
	}

	return response, nil
}

func withRetry(retries int, interval time.Duration, fn func(attempt, retries int) error) error {
	var err error
	for i := 0; i < retries; i++ {
		err = fn(i+1, retries)
		if err == nil {
			return nil
		}
		time.Sleep(interval)
	}

	return err
}
