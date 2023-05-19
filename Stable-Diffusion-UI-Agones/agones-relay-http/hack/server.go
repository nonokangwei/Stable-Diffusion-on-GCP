package main

import (
	"context"
	"encoding/json"
	"flag"
	"github.com/Octops/agones-relay-http/internal/runtime"
	"github.com/Octops/agones-relay-http/pkg/broker"
	"github.com/labstack/echo/v4"
	"github.com/labstack/echo/v4/middleware"
	"github.com/sirupsen/logrus"
	"net/http"
	"strings"
)

/*
curl --header "Content-Type: application/json" \
  --request POST \
  --data '{"username":"xyz","password":"xyz"}' \
  http://localhost:8090
*/

var (
	addr    string
	verbose bool
)

func init() {
	flag.StringVar(&addr, "addr", ":8090", "address for the server to be listening")
	flag.BoolVar(&verbose, "verbose", true, "show verbose logs")
}

type Logger func(c echo.Context) error

func logVerbose(c echo.Context) error {
	var payload broker.Payload
	if err := c.Bind(&payload); err != nil {
		logrus.Error(err)
		return echo.NewHTTPError(http.StatusBadRequest, "request body does not contain a valid payload")
	}

	p, err := json.Marshal(&payload)
	if err != nil {
		logrus.Error(err)
		return echo.NewHTTPError(http.StatusBadRequest, "request body does not contain a valid payload")
	}

	logrus.Infof("webhook received: %s/%s %s", strings.ToLower(payload.Body.Header.Headers["event_source"]), strings.ToLower(payload.Body.Header.Headers["event_type"]), p)
	return nil
}

func logAcknowledge(c echo.Context) error {
	var payload broker.Payload
	if err := c.Bind(&payload); err != nil {
		logrus.Error(err)
		return echo.NewHTTPError(http.StatusBadRequest, "request body does not contain a valid payload")
	}

	logrus.Infof("webhook received: %s/%s", strings.ToLower(payload.Body.Header.Headers["event_source"]), strings.ToLower(payload.Body.Header.Headers["event_type"]))
	return nil
}

func main() {
	flag.Parse()

	e := echo.New()
	e.Use(middleware.Recover())

	var logger Logger = logAcknowledge

	logrus.SetFormatter(&logrus.TextFormatter{})

	if verbose {
		e.Use(middleware.Logger())
		logrus.SetLevel(logrus.DebugLevel)
		logger = logVerbose
	}

	e.POST("/webhook", func(c echo.Context) error {
		if err := logger(c); err != nil {
			return err
		}

		return c.String(http.StatusOK, "OK")
	})

	e.PUT("/webhook", func(c echo.Context) error {
		if err := logger(c); err != nil {
			return err
		}

		return c.String(http.StatusOK, "OK")
	})

	e.DELETE("/webhook", func(c echo.Context) error {
		logrus.Infof("webhook received: ondelete/%s %s-%s", c.QueryParam("event_type"), c.QueryParam("namespace"), c.QueryParam("name"))
		return c.String(http.StatusOK, "OK")
	})

	go func() {
		if err := e.Start(addr); err != nil {
			e.Logger.Info("shutting down the server")
		}
	}()

	ctx, cancel := context.WithCancel(context.Background())
	runtime.SetupSignal(cancel)

	<-ctx.Done()

	defer cancel()

	logrus.Info("stopping server")
	if err := e.Shutdown(ctx); err != nil {
		e.Logger.Fatal(err)
	}
}
