FROM alpine:3.19 AS builder

RUN apk add --no-cache gcc musl-dev libmicrohttpd-dev make curl-dev

WORKDIR /app
COPY . .
RUN make clean && make

FROM alpine:3.19
RUN apk add --no-cache ca-certificates libmicrohttpd curl libcurl
WORKDIR /app
COPY --from=builder /app/c-template .
EXPOSE 3004
CMD ["./c-template"]
