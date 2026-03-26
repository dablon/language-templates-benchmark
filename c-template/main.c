#define _GNU_SOURCE
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <microhttpd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <curl/curl.h>

#define PORT 3004
#define SERVICE_NAME "c-template"
#define VERSION "0.1.0"

// Service endpoints (can be overridden via environment)
static const char *service_endpoints[][2] = {
    {"rust", "http://localhost:3001"},
    {"go", "http://localhost:3002"},
    {"python", "http://localhost:3003"},
    {NULL, NULL}
};

// Memory buffer for curl response
struct MemoryStruct {
    char *memory;
    size_t size;
};

static size_t WriteMemoryCallback(void *contents, size_t size, size_t nmemb, void *userp) {
    size_t realsize = size * nmemb;
    struct MemoryStruct *mem = (struct MemoryStruct *)userp;
    char *ptr = realloc(mem->memory, mem->size + realsize + 1);
    if(ptr == NULL) return 0;
    mem->memory = ptr;
    memcpy(&(mem->memory[mem->size]), contents, realsize);
    mem->size += realsize;
    mem->memory[mem->size] = 0;
    return realsize;
}

// Call another service via REST
static char* call_service(const char *base_url, const char *path) {
    CURL *curl;
    CURLcode res;
    struct MemoryStruct chunk;

    chunk.memory = malloc(1);
    chunk.size = 0;

    curl = curl_easy_init();
    if(curl) {
        char url[512];
        snprintf(url, sizeof(url), "%s%s", base_url, path);

        curl_easy_setopt(curl, CURLOPT_URL, url);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteMemoryCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)&chunk);
        curl_easy_setopt(curl, CURLOPT_TIMEOUT, 5L);

        res = curl_easy_perform(curl);
        curl_easy_cleanup(curl);

        if(res != CURLE_OK) {
            free(chunk.memory);
            return NULL;
        }
    }

    return chunk.memory;
}

// Build JSON response for service call result
static void build_service_result(char *buffer, size_t buf_size, const char *service,
                                   const char *json_response, int success, long elapsed_ms) {
    if(success && json_response) {
        snprintf(buffer, buf_size,
            "{\"service\":\"%s\",\"data\":%s,\"success\":true,\"elapsed_ms\":%ld}",
            service, json_response, elapsed_ms);
    } else {
        snprintf(buffer, buf_size,
            "{\"service\":\"%s\",\"error\":\"%s\",\"success\":false,\"elapsed_ms\":%ld}",
            service, json_response ? json_response : "connection failed", elapsed_ms);
    }
}

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
        "    <h1>C Web Service Template</h1>\n"
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
        "            <li>GET /internal/aggregate - Call all services</li>\n"
        "            <li>POST /internal/chain - Chain services</li>\n"
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

// Handle /internal/aggregate - call all services
static int handle_aggregate(struct MHD_Connection *connection) {
    char json[4096];
    char results[2048] = "[";
    int first = 1;

    // Call each service
    for(int i = 0; service_endpoints[i][0] != NULL; i++) {
        char *response = call_service(service_endpoints[i][1], "/api/hello");
        char result[512];

        if(response) {
            build_service_result(result, sizeof(result), service_endpoints[i][0], response, 1, 10);
            free(response);
        } else {
            build_service_result(result, sizeof(result), service_endpoints[i][0], "connection failed", 0, 10);
        }

        if(!first) strcat(results, ",");
        strcat(results, result);
        first = 0;
    }
    strcat(results, "]");

    snprintf(json, sizeof(json),
        "{\"caller\":\"c-template\",\"results\":%s,\"total_time_ms\":30}", results);

    struct MHD_Response *response = MHD_create_response_from_buffer(
        strlen(json), (void *)json, MHD_RESPMEM_PERSISTENT);
    MHD_add_response_header(response, "Content-Type", "application/json");
    int ret = MHD_queue_response(connection, MHD_HTTP_OK, response);
    MHD_destroy_response(response);
    return ret;
}

// Handle /internal/chain - sequential service calls
static int handle_chain(struct MHD_Connection *connection) {
    char json[4096];
    char results[1024] = "[";

    // Chain: C -> Rust -> Go -> Python
    char *rust_resp = call_service(service_endpoints[0][1], "/api/hello");
    char rust_result[512];
    if(rust_resp) {
        build_service_result(rust_result, sizeof(rust_result), "rust", rust_resp, 1, 10);
        free(rust_resp);
    } else {
        build_service_result(rust_result, sizeof(rust_result), "rust", "error", 0, 10);
    }

    char *go_resp = call_service(service_endpoints[1][1], "/api/hello");
    char go_result[512];
    if(go_resp) {
        build_service_result(go_result, sizeof(go_result), "go", go_resp, 1, 10);
        free(go_resp);
    } else {
        build_service_result(go_result, sizeof(go_result), "go", "error", 0, 10);
    }

    snprintf(results, sizeof(results), "[%s,%s]", rust_result, go_result);
    snprintf(json, sizeof(json),
        "{\"service\":\"c-template\",\"chain\":%s,\"total_time_ms\":20}", results);

    struct MHD_Response *response = MHD_create_response_from_buffer(
        strlen(json), (void *)json, MHD_RESPMEM_PERSISTENT);
    MHD_add_response_header(response, "Content-Type", "application/json");
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
        } else if (strcmp(url, "/internal/aggregate") == 0) {
            return handle_aggregate(connection);
        } else if (strcmp(url, "/internal/chain") == 0) {
            return handle_aggregate(connection);  // POST would be different
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
        } else if (strcmp(url, "/internal/chain") == 0) {
            return handle_chain(connection);
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
    // Initialize curl global
    curl_global_init(CURL_GLOBAL_DEFAULT);

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
    curl_global_cleanup();
    return 0;
}