#define _GNU_SOURCE
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <microhttpd.h>
#include <signal.h>
#include <time.h>
#include <unistd.h>

#define PORT 3004
#define SERVICE_NAME "{{PROJECT_NAME}}"
#define VERSION "0.1.0"

static struct MHD_Daemon *g_daemon = NULL;

static const char *get_env(const char *key, const char *default_value) {
    const char *value = getenv(key);
    return value ? value : default_value;
}

static enum MHD_Result send_response(struct MHD_Connection *connection, const char *data, int status_code) {
    struct MHD_Response *response = MHD_create_response_from_buffer(strlen(data), (void*)data, MHD_RESPMEM_MUST_COPY);
    if (!response) return MHD_NO;
    MHD_add_response_header(response, "Content-Type", "application/json");
    enum MHD_Result ret = MHD_queue_response(connection, status_code, response);
    MHD_destroy_response(response);
    return ret;
}

static enum MHD_Result handle_health(struct MHD_Connection *connection) {
    char response[256];
    snprintf(response, sizeof(response), "{\"status\":\"healthy\",\"service\":\"%s\",\"version\":\"%s\"}", SERVICE_NAME, VERSION);
    return send_response(connection, response, MHD_HTTP_OK);
}

static enum MHD_Result handle_hello(struct MHD_Connection *connection) {
    char response[512];
    snprintf(response, sizeof(response), "{\"message\":\"Hello from %s!\",\"service\":\"%s\",\"version\":\"%s\",\"timestamp\":%ld}", SERVICE_NAME, SERVICE_NAME, VERSION, (long)time(NULL));
    return send_response(connection, response, MHD_HTTP_OK);
}

static int is_prime(int n) {
    if (n < 2) return 0;
    for (int i = 2; i * i <= n; i++) if (n % i == 0) return 0;
    return 1;
}

static int fibonacci(int n) {
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

static enum MHD_Result handle_compute(struct MHD_Connection *connection, int n) {
    if (n > 35) n = 35;
    if (n < 1) n = 1;
    int fib = fibonacci(n);
    int primes_count = 0;
    for (int i = 2; i < n * 10 && primes_count < 100; i++) if (is_prime(i)) primes_count++;
    char response[512];
    snprintf(response, sizeof(response), "{\"operation\":\"compute\",\"fibonacci_input\":%d,\"fibonacci_value\":%d,\"primes_count\":%d,\"service\":\"%s\"}", n, fib, primes_count, SERVICE_NAME);
    return send_response(connection, response, MHD_HTTP_OK);
}

static enum MHD_Result handle_echo(struct MHD_Connection *connection, const char *body, size_t body_size) {
    char response[1024];
    char *upper = malloc(body_size + 1);
    char *lower = malloc(body_size + 1);
    if (!upper || !lower) {
        free(upper); free(lower);
        snprintf(response, sizeof(response), "{\"error\":\"memory error\"}");
        return send_response(connection, response, MHD_HTTP_INTERNAL_SERVER_ERROR);
    }
    for (size_t i = 0; i < body_size; i++) {
        upper[i] = (body[i] >= 'a' && body[i] <= 'z') ? body[i] - 32 : body[i];
        lower[i] = (body[i] >= 'A' && body[i] <= 'Z') ? body[i] + 32 : body[i];
    }
    upper[body_size] = '\0';
    lower[body_size] = '\0';
    snprintf(response, sizeof(response), "{\"original_length\":%zu,\"uppercase\":\"%s\",\"lowercase\":\"%s\",\"service\":\"%s\"}", body_size, upper, lower, SERVICE_NAME);
    free(upper); free(lower);
    return send_response(connection, response, MHD_HTTP_OK);
}

static enum MHD_Result handle_index(struct MHD_Connection *connection) {
    const char *html = "<!DOCTYPE html><html><head><title>" SERVICE_NAME "</title><style>body{font-family:Arial;margin:40px;background:#1a1a2e;color:#eee}h1{color:#4caf50}.card{background:#16213e;padding:20px;border-radius:8px;margin:10px 0}a{color:#4caf50}</style></head><body><h1>" SERVICE_NAME "</h1><div class=card><p>Version: " VERSION "</p><p>Protocol: HTTP</p><p>Language: C</p></div><div class=card><h3>Endpoints</h3><ul><li><a href=/health>/health</a></li><li><a href=/api/hello>/api/hello</a></li><li><a href=/api/compute?n=30>/api/compute</a></li><li>POST /api/echo</li></ul></div></body></html>";
    struct MHD_Response *response = MHD_create_response_from_buffer(strlen(html), (void*)html, MHD_RESPMEM_MUST_COPY);
    if (!response) return MHD_NO;
    MHD_add_response_header(response, "Content-Type", "text/html");
    enum MHD_Result ret = MHD_queue_response(connection, MHD_HTTP_OK, response);
    MHD_destroy_response(response);
    return ret;
}

static enum MHD_Result answer_to_connection(void *cls, struct MHD_Connection *connection, const char *url, const char *method, const char *version, const char *upload_data, size_t *upload_data_size, void **con_cls) {
    static int dummy;
    if (*con_cls == NULL) {
        *con_cls = &dummy;
        return MHD_YES;
    }
    *con_cls = NULL;
    
    if (strcmp(url, "/health") == 0 && strcmp(method, "GET") == 0) {
        return handle_health(connection);
    } else if (strcmp(url, "/api/hello") == 0 && strcmp(method, "GET") == 0) {
        return handle_hello(connection);
    } else if (strcmp(url, "/api/compute") == 0 && strcmp(method, "GET") == 0) {
        int n = 30;
        const char *query = strchr(url, '?');
        if (query) sscanf(query + 2, "n=%d", &n);
        return handle_compute(connection, n);
    } else if (strcmp(url, "/api/echo") == 0 && strcmp(method, "POST") == 0) {
        if (*upload_data_size > 0) {
            enum MHD_Result r = handle_echo(connection, upload_data, *upload_data_size);
            *upload_data_size = 0;
            return r;
        }
        return MHD_YES;
    } else if (strcmp(url, "/") == 0 && strcmp(method, "GET") == 0) {
        return handle_index(connection);
    }
    
    char not_found[64];
    snprintf(not_found, sizeof(not_found), "{\"error\":\"not found\"}");
    return send_response(connection, not_found, MHD_HTTP_NOT_FOUND);
}

static void signal_handler(int sig) {
    printf("\nShutting down...\n");
    if (g_daemon) MHD_stop_daemon(g_daemon);
    exit(0);
}

int main() {
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);
    int port = atoi(get_env("PORT", "3004"));
    printf("Starting %s (HTTP/C) on port %d\n", SERVICE_NAME, port);
    g_daemon = MHD_start_daemon(MHD_USE_SELECT_INTERNALLY, port, NULL, NULL, &answer_to_connection, NULL, MHD_OPTION_END);
    if (g_daemon == NULL) {
        fprintf(stderr, "Failed to start server on port %d\n", port);
        return 1;
    }
    printf("Server running on port %d (press Ctrl+C to stop)\n", port);
    while (1) sleep(1);
    return 0;
}
