CC = gcc
CFLAGS = -Wall -Wextra -O2 -pthread
LDFLAGS = -lmicrohttpd -lcurl -pthread

TARGET = c-template
SRC = main.c
OBJ = $(SRC:.c=.o)

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CC) $(OBJ) $(LDFLAGS) -o $@

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(TARGET) $(OBJ)
