/**
 * Configuration implementation
 */

#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "include/config.h"
#include "include/response.h"

struct Config* config_create(int port, const char *service_name, const char *version) {
    struct Config *config = (struct Config *)malloc(sizeof(struct Config));
    if (!config) {
        return NULL;
    }

    config->port = port;
    config->service_name = strdup(service_name);
    config->version = strdup(version);
    config->static_dir = strdup("./static");
    config->thread_pool_size = DEFAULT_THREAD_POOL_SIZE;
    config->timeout_seconds = DEFAULT_TIMEOUT;

    return config;
}

void config_destroy(struct Config *config) {
    if (config) {
        free(config->service_name);
        free(config->version);
        free(config->static_dir);
        free(config);
    }
}