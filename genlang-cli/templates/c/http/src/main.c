/**
 * Main Entry Point
 * C HTTP Web Service - Clean Architecture
 */

#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>

#include "config.h"
#include "routes.h"

static struct MHD_Daemon *g_daemon = NULL;

static void signal_handler(int sig) {
    (void)sig;
    printf("\nShutting down...\n");
    if (g_daemon) MHD_stop_daemon(g_daemon);
    exit(0);
}

int main() {
    // Setup signal handlers
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    // Get port from environment or use default
    int port = get_port();

    printf("Starting %s (HTTP/C) on port %d\n", SERVICE_NAME, port);

    // Start HTTP server
    g_daemon = MHD_start_daemon(
        MHD_USE_SELECT_INTERNALLY,
        port,
        NULL,
        NULL,
        &handle_request,
        NULL,
        MHD_OPTION_END
    );

    if (g_daemon == NULL) {
        fprintf(stderr, "Failed to start server on port %d\n", port);
        return 1;
    }

    printf("Server running on port %d (press Ctrl+C to stop)\n", port);

    // Keep running
    while (1) sleep(1);

    return 0;
}