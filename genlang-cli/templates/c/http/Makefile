CC = gcc
CFLAGS = -Wall -O2 -std=c11 -Iinclude
LDFLAGS = -lmicrohttpd

TARGET = server
SRC_DIR = src
SRC = $(SRC_DIR)/main.c $(SRC_DIR)/config.c $(SRC_DIR)/handlers/routes.c

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC) $(LDFLAGS)

clean:
	rm -f $(TARGET)

run: $(TARGET)
	./$(TARGET)

test:
	@echo "Tests placeholder - run manually"

.PHONY: all clean run test