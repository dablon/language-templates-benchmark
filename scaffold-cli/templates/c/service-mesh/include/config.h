/**
 * Configuration header for C template
 */

#ifndef CONFIG_H
#define CONFIG_H

#include <stddef.h>

// Configuration structure
struct Config {
    int port;
    char *service_name;
    char *version;
    char *static_dir;
    int max_connections;
    int thread_pool_size;
    int timeout_seconds;
};

// Create configuration
struct Config* config_create(int port, const char *service_name, const char *version);

// Destroy configuration
void config_destroy(struct Config *config);

// Default values
#define DEFAULT_PORT 3004
#define DEFAULT_THREAD_POOL_SIZE 4
#define DEFAULT_TIMEOUT 30

#endif // CONFIG_H