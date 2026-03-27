/**
 * Route handlers header
 */

#ifndef ROUTES_H
#define ROUTES_H

#include <microhttpd.h>

/**
 * Main request handler - routes requests to appropriate handlers
 */
enum MHD_Result handle_request(
    void *cls,
    struct MHD_Connection *connection,
    const char *url,
    const char *method,
    const char *version,
    const char *upload_data,
    size_t *upload_data_size,
    void **con_cls
);

/**
 * Health check handler
 */
enum MHD_Result handle_health(struct MHD_Connection *connection);

/**
 * Hello endpoint handler
 */
enum MHD_Result handle_hello(struct MHD_Connection *connection);

/**
 * Compute benchmark handler
 */
enum MHD_Result handle_compute(struct MHD_Connection *connection, int n);

/**
 * Echo handler
 */
enum MHD_Result handle_echo(struct MHD_Connection *connection, const char *body, size_t body_size);

/**
 * Index page handler
 */
enum MHD_Result handle_index(struct MHD_Connection *connection);

#endif // ROUTES_H