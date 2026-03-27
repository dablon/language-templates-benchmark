# Build stage
FROM golang:1.23-alpine AS builder

RUN apk add --no-cache git protobuf protoc

# Force local toolchain
ENV GOTOOLCHAIN=local

# Install Go protoc plugins with versions that work with Go 1.23
RUN go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.33.0 && \
    go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.3.0

# Create symlinks with the naming convention protoc expects
RUN ln -sf $(go env GOPATH)/bin/protoc-gen-go-grpc $(go env GOPATH)/bin/protoc-gen-grpc-go || true

# Add GOPATH/bin to PATH so protoc can find the plugins
ENV PATH="$(go env GOPATH)/bin:${PATH}"

WORKDIR /app

# Install Go dependencies
COPY go.mod go.sum* ./
RUN go mod download

# Copy source
COPY . .

# Generate proto files
RUN protoc --go_out=. --go_opt=paths=source_relative \
           --grpc-go_out=. --grpc-go_opt=paths=source_relative \
           benchmark.proto

# Build
RUN CGO_ENABLED=0 GOOS=linux go build -o server main.go

# Runtime stage
FROM alpine:latest

RUN apk add --no-cache ca-certificates

WORKDIR /app

COPY --from=builder /app/server .
COPY --from=builder /app/benchmark.proto .

EXPOSE 3002

CMD ["./server"]