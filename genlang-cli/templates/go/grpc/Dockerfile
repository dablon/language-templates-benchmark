# Build stage
FROM golang:1.23-alpine AS builder

RUN apk add --no-cache git protobuf protoc

ENV PATH="/root/go/bin:$(go env GOPATH)/bin:${PATH}"
ENV GOTOOLCHAIN=local

RUN go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.33.0 && \
    go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.3.0

RUN ln -sf $(go env GOPATH)/bin/protoc-gen-go-grpc $(go env GOPATH)/bin/protoc-gen-grpc-go || true

WORKDIR /app

COPY go.mod go.sum* ./
RUN go mod download

COPY . .

# Generate proto files in current directory
RUN protoc --go_out=. --go_opt=paths=source_relative \
           --grpc-go_out=. --grpc-go_opt=paths=source_relative \
           benchmark.proto

# Fix go.mod and build
RUN go mod tidy
RUN CGO_ENABLED=0 GOOS=linux go build -o server .

# Runtime stage
FROM alpine:latest
RUN apk add --no-cache ca-certificates
WORKDIR /app
COPY --from=builder /app/server .
COPY --from=builder /app/benchmark.proto .
EXPOSE 3002
CMD ["./server"]