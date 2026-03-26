# Build stage
FROM golang:1.21-alpine AS builder

RUN apk add --no-cache git protobuf protoc

WORKDIR /app

# Install Go dependencies
COPY go.mod go.sum ./
RUN go mod download

# Copy source
COPY . .

# Generate proto files
RUN protoc --go_out=. --go_opt=paths=source_relative --grpc-go_out=. --grpc-go_opt=paths=source_relative benchmark.proto

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
