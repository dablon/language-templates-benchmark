/**
 * Route handlers implementation
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

#include "routes.h"
#include "config.h"

// =============================================================================
// Helper Functions
// =============================================================================

static enum MHD_Result send_json_response(
    struct MHD_Connection *connection,
    const char *json_data,
    int status_code
) {
    struct MHD_Response *response = MHD_create_response_from_buffer(
        strlen(json_data),
        (void*)json_data,
        MHD_RESPMEM_MUST_COPY
    );
    if (!response) return MHD_NO;

    MHD_add_response_header(response, "Content-Type", "application/json");
    enum MHD_Result ret = MHD_queue_response(connection, status_code, response);
    MHD_destroy_response(response);
    return ret;
}

// =============================================================================
// Health Handler
// =============================================================================

enum MHD_Result handle_health(struct MHD_Connection *connection) {
    char response[256];
    snprintf(response, sizeof(response),
        "{\"status\":\"healthy\",\"service\":\"%s\",\"version\":\"%s\"}",
        SERVICE_NAME, VERSION
    );
    return send_json_response(connection, response, MHD_HTTP_OK);
}

// =============================================================================
// Hello Handler
// =============================================================================

enum MHD_Result handle_hello(struct MHD_Connection *connection) {
    char response[512];
    snprintf(response, sizeof(response),
        "{\"message\":\"Hello from %s!\",\"service\":\"%s\",\"version\":\"%s\",\"timestamp\":%ld}",
        SERVICE_NAME, SERVICE_NAME, VERSION, (long)time(NULL)
    );
    return send_json_response(connection, response, MHD_HTTP_OK);
}

// =============================================================================
// Compute Service (Business Logic)
// =============================================================================

static int is_prime(int n) {
    if (n < 2) return 0;
    for (int i = 2; i * i <= n; i++) {
        if (n % i == 0) return 0;
    }
    return 1;
}

static int fibonacci(int n) {
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

// =============================================================================
// Compute Handler
// =============================================================================

enum MHD_Result handle_compute(struct MHD_Connection *connection, int n) {
    // Validate input
    if (n > 35) n = 35;
    if (n < 1) n = 1;

    // Calculate fibonacci
    int fib = fibonacci(n);

    // Count primes
    int primes_count = 0;
    for (int i = 2; i < n * 10 && primes_count < 100; i++) {
        if (is_prime(i)) primes_count++;
    }

    char response[512];
    snprintf(response, sizeof(response),
        "{\"operation\":\"compute\",\"fibonacci_input\":%d,\"fibonacci_value\":%d,\"primes_count\":%d,\"service\":\"%s\"}",
        n, fib, primes_count, SERVICE_NAME
    );

    return send_json_response(connection, response, MHD_HTTP_OK);
}

// =============================================================================
// Echo Service (Business Logic)
// =============================================================================

static void to_upper(const char *src, char *dest, size_t len) {
    for (size_t i = 0; i < len; i++) {
        if (src[i] >= 'a' && src[i] <= 'z') {
            dest[i] = src[i] - 32;
        } else {
            dest[i] = src[i];
        }
    }
    dest[len] = '\0';
}

static void to_lower(const char *src, char *dest, size_t len) {
    for (size_t i = 0; i < len; i++) {
        if (src[i] >= 'A' && src[i] <= 'Z') {
            dest[i] = src[i] + 32;
        } else {
            dest[i] = src[i];
        }
    }
    dest[len] = '\0';
}

// =============================================================================
// Echo Handler
// =============================================================================

enum MHD_Result handle_echo(struct MHD_Connection *connection, const char *body, size_t body_size) {
    char *upper = malloc(body_size + 1);
    char *lower = malloc(body_size + 1);

    if (!upper || !lower) {
        free(upper);
        free(lower);
        return send_json_response(connection, "{\"error\":\"memory error\"}", MHD_HTTP_INTERNAL_SERVER_ERROR);
    }

    to_upper(body, upper, body_size);
    to_lower(body, lower, body_size);

    char response[2048];
    snprintf(response, sizeof(response),
        "{\"original_length\":%zu,\"uppercase\":\"%s\",\"lowercase\":\"%s\",\"service\":\"%s\"}",
        body_size, upper, lower, SERVICE_NAME
    );

    free(upper);
    free(lower);

    return send_json_response(connection, response, MHD_HTTP_OK);
}

// =============================================================================
// Index Handler
// =============================================================================

enum MHD_Result handle_index(struct MHD_Connection *connection) {
    const char *html = "<!DOCTYPE html>"
        "<html>"
        "<head>"
        "<title>" SERVICE_NAME "</title>"
        "<style>"
        "body{font-family:Arial;margin:40px;background:#1a1a2e;color:#eee}"
        "h1{color:#4caf50}"
        ".card{background:#16213e;padding:20px;border-radius:8px;margin:10px 0}"
        "a{color:#4caf50}"
        "</style>"
        "</head>"
        "<body>"
        "<h1>" SERVICE_NAME "</h1>"
        "<div class=card>"
        "<p>Version: " VERSION "</p>"
        "<p>Protocol: HTTP</p>"
        "<p>Language: C</p>"
        "</div>"
        "<div class=card>"
        "<h3>Endpoints</h3>"
        "<ul>"
        "<li><a href=/health>/health</a></li>"
        "<li><a href=/api/hello>/api/hello</a></li>"
        "<li><a href=/api/compute?n=30>/api/compute</a></li>"
        "<li>POST /api/echo</li>"
        "</ul>"
        "</div>"
        "</body>"
        "</html>";

    struct MHD_Response *response = MHD_create_response_from_buffer(
        strlen(html),
        (void*)html,
        MHD_RESPMEM_MUST_COPY
    );

    if (!response) return MHD_NO;

    MHD_add_response_header(response, "Content-Type", "text/html");
    enum MHD_Result ret = MHD_queue_response(connection, MHD_HTTP_OK, response);
    MHD_destroy_response(response);
    return ret;
}

// =============================================================================
// Main Request Router
// =============================================================================

enum MHD_Result handle_request(
    void *cls,
    struct MHD_Connection *connection,
    const char *url,
    const char *method,
    const char *version,
    const char *upload_data,
    size_t *upload_data_size,
    void **con_cls
) {
    (void)cls;
    (void)version;

    // First call - just accept
    if (*con_cls == NULL) {
        static int dummy;
        *con_cls = &dummy;
        return MHD_YES;
    }
    *con_cls = NULL;

    // Route: GET /health
    if (strcmp(url, "/health") == 0 && strcmp(method, "GET") == 0) {
        return handle_health(connection);
    }

    // Route: GET /api/hello
    if (strcmp(url, "/api/hello") == 0 && strcmp(method, "GET") == 0) {
        return handle_hello(connection);
    }

    // Route: GET /api/compute
    if (strcmp(url, "/api/compute") == 0 && strcmp(method, "GET") == 0) {
        int n = 30;
        const char *query = strchr(url, '?');
        if (query) sscanf(query + 2, "n=%d", &n);
        return handle_compute(connection, n);
    }

    // Route: POST /api/echo
    if (strcmp(url, "/api/echo") == 0 && strcmp(method, "POST") == 0) {
        if (*upload_data_size > 0) {
            enum MHD_Result r = handle_echo(connection, upload_data, *upload_data_size);
            *upload_data_size = 0;
            return r;
        }
        return MHD_YES;
    }

    // Route: GET /
    if (strcmp(url, "/") == 0 && strcmp(method, "GET") == 0) {
        return handle_index(connection);
    }

    // 404 Not Found
    return send_json_response(connection, "{\"error\":\"not found\"}", MHD_HTTP_NOT_FOUND);
}