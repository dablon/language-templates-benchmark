/**
 * Configuration implementation
 */

#include <stdlib.h>
#include <stdio.h>
#include "config.h"

int get_port(void) {
    const char *port_env = getenv("PORT");
    if (port_env) {
        int port = atoi(port_env);
        if (port > 0 && port <= 65535) {
            return port;
        }
    }
    return DEFAULT_PORT;
}