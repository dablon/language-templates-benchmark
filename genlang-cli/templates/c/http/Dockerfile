FROM alpine:latest

RUN apk add --no-cache gcc musl-dev libmicrohttpd-dev make

WORKDIR /app

COPY . .
RUN make

EXPOSE 3004

CMD ["./server"]
