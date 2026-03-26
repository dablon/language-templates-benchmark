FROM alpine:3.19 AS builder

RUN apk add --no-cache gcc musl-dev libmicrohttpd-dev make

WORKDIR /app
COPY . .
RUN make clean && make

FROM alpine:3.19
RUN apk add --no-cache ca-certificates
WORKDIR /app
COPY --from=builder /app/c-template .
EXPOSE 3004
CMD ["./c-template"]
