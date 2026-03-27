/**
 * C Web Service Template - Main Entry Point
 * 
 * A high-performance web service using libmicrohttpd.
 * Part of the Language Templates Benchmark project.
 */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <microhttpd.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>

#include "include/config.h"
#include "include/routes.h"
#include "include/response.h"

#define PORT 3004
#define SERVICE_NAME "c-template"
#define VERSION "0.1.0"

static int running = 1;

void handle_signal(int sig) {
    (void)sig;
    running = 0;
}

int main() {
    struct MHD_Daemon *daemon;
    char port_str[16];

    // Set up signal handlers for graceful shutdown
    signal(SIGINT, handle_signal);
    signal(SIGTERM, handle_signal);

    // Convert port to string
    snprintf(port_str, sizeof(port_str), "%d", PORT);

    // Load configuration
    struct Config *config = config_create(PORT, SERVICE_NAME, VERSION);
    if (!config) {
        fprintf(stderr, "Failed to create configuration\n");
        return 1;
    }

    printf("Starting %s v%s on port %d\n", 
           config->service_name, config->version, config->port);

    // DAemon mode - use select() internally with internal threads
    daemon = MHD_start_daemon(
        MHD_USE_SELECT_INTERNALLY,
        config->port,
        NULL, NULL,
        &answer_to_connection,
        NULL,
        MHD_OPTION_THREADED, MHD_YES,
        MHD_OPTION_END
    );

    if (daemon == NULL) {
        fprintf(stderr, "Failed to start server on port %d\n", config->port);
        config_destroy(config);
        return 1;
    }

    printf("Server started. Press Ctrl+C to stop.\n");

    // Wait for shutdown signal
    while (running) {
        sleep(1);
    }

    printf("\nShutting down server...\n");

    MHD_stop_daemon(daemon);
    config_destroy(config);

    printf("Server stopped.\n");
    return 0;
}