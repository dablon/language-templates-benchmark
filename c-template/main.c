#define _GNU_SOURCE
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <microhttpd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>

#define PORT 3004
#define SERVICE_NAME "c-template"
#define VERSION "0.1.0"

static int handle_index(struct MHD_Connection *connection) {
    const char *html =
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "    <meta charset=\"UTF-8\">\n"
        "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
        "    <title>C Template - Web Service</title>\n"
        "    <style>\n"
        "        body { font-family: Arial, sans-serif; margin: 40px; background: #1a1a2e; color: #eee; }\n"
        "        h1 { color: #ff6b6b; }\n"
        "        .card { background: #16213e; padding: 20px; border-radius: 8px; margin: 10px 0; }\n"
        "        code { background: #0f3460; padding: 2px 6px; border-radius: 4px; }\n"
        "        a { color: #ff6b6b; }\n"
        "    </style>\n"
        "</head>\n"
        "<body>\n"
        "    <h1>⚙️ C Web Service Template</h1>\n"
        "    <div class=\"card\">\n"
        "        <h2>Language: C</h2>\n"
        "        <p>Library: <code>libmicrohttpd</code></p>\n"
        "        <p>Port: <code>3004</code></p>\n"
        "    </div>\n"
        "    <div class=\"card\">\n"
        "        <h2>Endpoints</h2>\n"
        "        <ul>\n"
        "            <li><a href=\"/health\">GET /health</a> - Health check</li>\n"
        "            <li><a href=\"/api/hello\">GET /api/hello</a> - JSON response</li>\n"
        "            <li>POST /api/echo - Echo body</li>\n"
        "        </ul>\n"
        "    </div>\n"
        "</body>\n"
        "</html>";

    struct MHD_Response *response = MHD_create_response_from_buffer(
        strlen(html), (void *)html, MHD_RESPMEM_PERSISTENT);
    MHD_add_response_header(response, "Content-Type", "text/html");
    int ret = MHD_queue_response(connection, MHD_HTTP_OK, response);
    MHD_destroy_response(response);
    return ret;
}

static int handle_health(struct MHD_Connection *connection) {
    const char *json = "{\"status\":\"healthy\",\"service\":\"c-template\"}";

    struct MHD_Response *response = MHD_create_response_from_buffer(
        strlen(json), (void *)json, MHD_RESPMEM_PERSISTENT);
    MHD_add_response_header(response, "Content-Type", "application/json");
    int ret = MHD_queue_response(connection, MHD_HTTP_OK, response);
    MHD_destroy_response(response);
    return ret;
}

static int handle_hello(struct MHD_Connection *connection) {
    const char *json = "{\"message\":\"Hello from C!\",\"service\":\"c-template\",\"version\":\"0.1.0\"}";

    struct MHD_Response *response = MHD_create_response_from_buffer(
        strlen(json), (void *)json, MHD_RESPMEM_PERSISTENT);
    MHD_add_response_header(response, "Content-Type", "application/json");
    int ret = MHD_queue_response(connection, MHD_HTTP_OK, response);
    MHD_destroy_response(response);
    return ret;
}

static int handle_echo(struct MHD_Connection *connection) {
    size_t data_size = 0;
    const char *data = MHD_post_processing_get_value(connection, "body");

    if (data == NULL) {
        /* Try to read raw data */
        data = MHD_connection_read(connection);
        if (data == NULL) {
            return MHD_NO;
        }
        data_size = strlen(data);
    } else {
        data_size = strlen(data);
    }

    struct MHD_Response *response = MHD_create_response_from_buffer(
        data_size, (void *)data, MHD_RESPMEM_PERSISTENT);
    int ret = MHD_queue_response(connection, MHD_HTTP_OK, response);
    MHD_destroy_response(response);
    return ret;
}

static int answer_to_connection(void *cls, struct MHD_Connection *connection,
                                const char *url, const char *method,
                                const char *version, const char *upload_data,
                                size_t *upload_data_size, void **con_cls) {

    (void)cls;
    (void)version;
    (void)upload_data;

    if (strcmp(method, "GET") == 0) {
        if (strcmp(url, "/") == 0) {
            return handle_index(connection);
        } else if (strcmp(url, "/health") == 0) {
            return handle_health(connection);
        } else if (strcmp(url, "/api/hello") == 0) {
            return handle_hello(connection);
        }
    } else if (strcmp(method, "POST") == 0) {
        if (strcmp(url, "/api/echo") == 0) {
            if (*upload_data_size != 0) {
                struct MHD_Response *response = MHD_create_response_from_buffer(
                    *upload_data_size, (void *)upload_data, MHD_RESPMEM_PERSISTENT);
                int ret = MHD_queue_response(connection, MHD_HTTP_OK, response);
                MHD_destroy_response(response);
                *upload_data_size = 0;
                return ret;
            }
        }
    }

    const char *not_found = "404 Not Found";
    struct MHD_Response *response = MHD_create_response_from_buffer(
        strlen(not_found), (void *)not_found, MHD_RESPMEM_PERSISTENT);
    int ret = MHD_queue_response(connection, MHD_HTTP_NOT_FOUND, response);
    MHD_destroy_response(response);
    return ret;
}

int main() {
    struct MHD_Daemon *daemon;

    daemon = MHD_start_daemon(MHD_USE_SELECT_INTERNALLY, PORT, NULL, NULL,
                             &answer_to_connection, NULL, MHD_OPTION_END);

    if (daemon == NULL) {
        fprintf(stderr, "Failed to start server\n");
        return 1;
    }

    printf("C template listening on port %d\n", PORT);
    getchar();

    MHD_stop_daemon(daemon);
    return 0;
}
