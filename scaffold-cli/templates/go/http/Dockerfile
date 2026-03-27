FROM golang:1.21-alpine AS builder

WORKDIR /app

# Create module path directory structure
RUN mkdir -p /go/src
WORKDIR /go/src

COPY go.mod go.sum* ./
RUN go mod download

COPY cmd/ ./cmd/
COPY internal/ ./internal/
COPY pkg/ ./pkg/
COPY static/ ./static/
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /app/service .

FROM alpine:3.19
RUN apk add --no-cache ca-certificates
WORKDIR /app
COPY --from=builder /app/service .
EXPOSE 3002
CMD ["./service"]
