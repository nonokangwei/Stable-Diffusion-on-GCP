FROM golang:1.17 AS builder

WORKDIR /go/src/github.com/Octops/agones-relay-http

COPY . .

RUN make build && chmod +x /go/src/github.com/Octops/agones-relay-http/bin/agones-relay-http

FROM alpine

WORKDIR /app

COPY --from=builder /go/src/github.com/Octops/agones-relay-http/bin/agones-relay-http /app/

ENTRYPOINT ["./agones-relay-http"]