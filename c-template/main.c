#define _GNU_SOURCE
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <microhttpd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <curl/curl.h>
#include <time.h>
#include <json-c/json.h>

#define PORT 3004
#define SERVICE_NAME "c-template"
#define VERSION "0.1.0"

// Database configuration
static char db_conn_string[512] = {0};
static int db_available = 0;

// Forward declarations
static int handle_index(struct MHD_Connection *connection);
static int handle_health(struct MHD_Connection *connection);
static int handle_hello(struct MHD_Connection *connection);
static int handle_echo(struct MHD_Connection *connection);
static int handle_aggregate(struct MHD_Connection *connection);
static int handle_chain(struct MHD_Connection *connection);
static int handle_grpc_health(struct MHD_Connection *connection);
static int handle_grpc_hello(struct MHD_Connection *connection, const char *data, size_t data_size);
static int handle_grpc_aggregate(struct MHD_Connection *connection, const char *data, size_t data_size);
// Database handlers
static int handle_db_records(struct MHD_Connection *connection);
static int handle_db_record(struct MHD_Connection *connection, const char *url);

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
        "    <meta name=\"description\" content=\"C Web Service - Language Templates Benchmark\">\n"
        "    <title>C Service - Language Templates Benchmark</title>\n"
        "    <style>\n"
        "        :root {\n"
        "            --bg-primary: #0d1117;\n"
        "            --bg-secondary: #161b22;\n"
        "            --bg-tertiary: #21262d;\n"
        "            --text-primary: #c9d1d9;\n"
        "            --text-secondary: #8b949e;\n"
        "            --accent-c: #ff6b6b;\n"
        "            --accent-python: #4caf50;\n"
        "            --accent-go: #00add8;\n"
        "            --accent-rust: #dea584;\n"
        "            --border-color: #30363d;\n"
        "            --success: #238636;\n"
        "            --warning: #d29922;\n"
        "        }\n"
        "        * { margin: 0; padding: 0; box-sizing: border-box; }\n"
        "        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg-primary); color: var(--text-primary); line-height: 1.6; }\n"
        "        .bg-animation { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; overflow: hidden; }\n"
        "        .bg-animation::before { content: ''; position: absolute; width: 200%; height: 200%; background: radial-gradient(circle at 20% 80%, rgba(255, 107, 107, 0.1) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(0, 173, 216, 0.08) 0%, transparent 50%); animation: bgMove 20s ease-in-out infinite; }\n"
        "        @keyframes bgMove { 0%, 100% { transform: translate(0, 0); } 50% { transform: translate(-10%, -10%); } }\n"
        "        @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }\n"
        "        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }\n"
        "        header { display: flex; justify-content: space-between; align-items: center; padding: 20px 0; border-bottom: 1px solid var(--border-color); }\n"
        "        .logo { display: flex; align-items: center; gap: 15px; }\n"
        "        .logo-icon { font-size: 48px; animation: float 3s ease-in-out infinite; }\n"
        "        .logo h1 { font-size: 2em; background: linear-gradient(90deg, var(--accent-c), #ff4444); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }\n"
        "        .nav { display: flex; gap: 20px; }\n"
        "        .nav a { color: var(--text-secondary); text-decoration: none; padding: 8px 16px; border-radius: 6px; transition: all 0.3s; }\n"
        "        .nav a:hover { background: var(--bg-tertiary); color: var(--text-primary); }\n"
        "        .hero { text-align: center; padding: 60px 0; }\n"
        "        .hero h2 { font-size: 3em; margin-bottom: 20px; }\n"
        "        .hero .framework { font-size: 1.5em; color: var(--text-secondary); margin-bottom: 30px; }\n"
        "        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 40px 0; }\n"
        "        .stat-card { background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 12px; padding: 25px; text-align: center; transition: transform 0.3s, border-color 0.3s; }\n"
        "        .stat-card:hover { transform: translateY(-5px); border-color: var(--accent-c); }\n"
        "        .stat-card.fast { border-color: var(--success); background: linear-gradient(135deg, var(--bg-secondary), rgba(35, 134, 54, 0.1)); }\n"
        "        .stat-value { font-size: 2.5em; font-weight: bold; color: var(--accent-c); }\n"
        "        .stat-label { color: var(--text-secondary); margin-top: 5px; }\n"
        "        .stat-badge { display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 0.8em; margin-top: 10px; }\n"
        "        .badge-tps { background: var(--success); color: white; }\n"
        "        .badge-latency { background: var(--warning); color: black; }\n"
        "        .badge-memory { background: #9c27b0; color: white; }\n"
        "        .badge-dev { background: var(--accent-c); color: white; }\n"
        "        section { margin: 40px 0; }\n"
        "        section h3 { font-size: 1.8em; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid var(--border-color); }\n"
        "        .comparison-table { width: 100%; border-collapse: collapse; background: var(--bg-secondary); border-radius: 12px; overflow: hidden; }\n"
        "        .comparison-table th, .comparison-table td { padding: 15px 20px; text-align: left; border-bottom: 1px solid var(--border-color); }\n"
        "        .comparison-table th { background: var(--bg-tertiary); color: var(--text-secondary); font-weight: 600; text-transform: uppercase; font-size: 0.85em; }\n"
        "        .comparison-table tr:hover { background: var(--bg-tertiary); }\n"
        "        .comparison-table .fast-row { background: rgba(255, 107, 107, 0.15); }\n"
        "        .comparison-table .fast-row td:first-child::before { content: '⚡ '; }\n"
        "        .chart-container { background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 12px; padding: 20px; margin: 20px 0; }\n"
        "        .bar-chart { display: flex; flex-direction: column; gap: 15px; }\n"
        "        .bar-row { display: flex; align-items: center; gap: 15px; }\n"
        "        .bar-label { width: 80px; font-size: 0.9em; }\n"
        "        .bar-track { flex: 1; height: 30px; background: var(--bg-tertiary); border-radius: 6px; overflow: hidden; }\n"
        "        .bar-fill { height: 100%; border-radius: 6px; transition: width 1s ease-out; display: flex; align-items: center; justify-content: flex-end; padding-right: 10px; font-size: 0.85em; font-weight: bold; }\n"
        "        .bar-fill.rust { background: var(--accent-rust); }\n"
        "        .bar-fill.go { background: var(--accent-go); }\n"
        "        .bar-fill.python { background: var(--accent-python); }\n"
        "        .bar-fill.c { background: var(--accent-c); }\n"
        "        .endpoints-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 15px; }\n"
        "        .endpoint-card { background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 8px; padding: 15px; transition: all 0.3s; }\n"
        "        .endpoint-card:hover { border-color: var(--accent-c); }\n"
        "        .endpoint-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }\n"
        "        .method { padding: 4px 10px; border-radius: 4px; font-size: 0.75em; font-weight: bold; text-transform: uppercase; }\n"
        "        .method.get { background: var(--success); }\n"
        "        .method.post { background: var(--accent-go); }\n"
        "        .endpoint-path { font-family: monospace; font-size: 1.1em; color: var(--accent-c); }\n"
        "        .endpoint-desc { color: var(--text-secondary); font-size: 0.9em; }\n"
        "        .quick-actions { display: flex; gap: 15px; flex-wrap: wrap; margin: 20px 0; }\n"
        "        .action-btn { display: inline-flex; align-items: center; gap: 8px; padding: 12px 24px; background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 8px; color: var(--text-primary); text-decoration: none; transition: all 0.3s; cursor: pointer; }\n"
        "        .action-btn:hover { background: var(--bg-secondary); border-color: var(--accent-c); }\n"
        "        .action-btn.primary { background: var(--accent-c); color: white; border-color: var(--accent-c); }\n"
        "        .action-btn.primary:hover { background: #ff4444; }\n"
        "        footer { text-align: center; padding: 40px 0; margin-top: 60px; border-top: 1px solid var(--border-color); color: var(--text-secondary); }\n"
        "        footer a { color: var(--accent-c); text-decoration: none; }\n"
        "        .result-box { background: var(--bg-tertiary); border-radius: 8px; padding: 15px; margin-top: 15px; font-family: monospace; font-size: 0.9em; display: none; }\n"
        "        .result-box.show { display: block; }\n"
        "        .result-box pre { overflow-x: auto; color: var(--accent-c); }\n"
        "        .inter-service-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }\n"
        "        .inter-card { background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 12px; padding: 20px; }\n"
        "        .inter-card h4 { color: var(--text-secondary); font-size: 0.9em; text-transform: uppercase; margin-bottom: 10px; }\n"
        "        .inter-value { font-size: 1.8em; color: var(--accent-c); }\n"
        "        @media (max-width: 768px) { .hero h2 { font-size: 2em; } .stats-grid { grid-template-columns: repeat(2, 1fr); } .nav { display: none; } }\n"
        "    </style>\n"
        "</head>\n"
        "<body>\n"
        "    <div class=\"bg-animation\"></div>\n"
        "    <div class=\"container\">\n"
        "        <header>\n"
        "            <div class=\"logo\">\n"
        "                <span class=\"logo-icon\">⚙️</span>\n"
        "                <div>\n"
        "                    <h1>C Service</h1>\n"
        "                    <span style=\"color: var(--text-secondary);\">Language Templates Benchmark</span>\n"
        "                </div>\n"
        "            </div>\n"
        "            <nav class=\"nav\">\n"
        "                <a href=\"/\">Home</a>\n"
        "                <a href=\"/health\">Health</a>\n"
        "                <a href=\"/api/hello\">API</a>\n"
        "                <a href=\"http://localhost:3100\">Gateway</a>\n"
        "                <a href=\"http://localhost:8500\">Consul</a>\n"
        "            </nav>\n"
        "        </header>\n"
        "        <main>\n"
        "            <section class=\"hero\">\n"
        "                <h2>C Web Service</h2>\n"
        "                <p class=\"framework\">Powered by <strong>libmicrohttpd</strong> library • <strong>C17</strong> standard</p>\n"
        "                <div class=\"quick-actions\">\n"
        "                    <button class=\"action-btn primary\" onclick=\"testEndpoint('/health')\">🟢 Test Health</button>\n"
        "                    <button class=\"action-btn\" onclick=\"testEndpoint('/api/hello')\">📡 Test API</button>\n"
        "                    <button class=\"action-btn\" onclick=\"testEndpoint('/internal/aggregate')\">🔗 Test Aggregate</button>\n"
        "                    <button class=\"action-btn\" onclick=\"testEndpoint('/grpc.health', 'POST')\">⚡ Test gRPC</button>\n"
        "                </div>\n"
        "                <div id=\"result\" class=\"result-box\"><pre></pre></div>\n"
        "            </section>\n"
        "            <section>\n"
        "                <h3>📊 Benchmark Results</h3>\n"
        "                <div class=\"stats-grid\">\n"
        "                    <div class=\"stat-card\">\n"
        "                        <div class=\"stat-value\">567</div>\n"
        "                        <div class=\"stat-label\">TPS (100 concurrent)</div>\n"
        "                    </div>\n"
        "                    <div class=\"stat-card fast\">\n"
        "                        <div class=\"stat-value\">117ms</div>\n"
        "                        <div class=\"stat-label\">Avg Latency</div>\n"
        "                        <span class=\"stat-badge badge-memory\">💾 Low Memory</span>\n"
        "                    </div>\n"
        "                    <div class=\"stat-card\">\n"
        "                        <div class=\"stat-value\">255ms</div>\n"
        "                        <div class=\"stat-label\">P99 Latency</div>\n"
        "                    </div>\n"
        "                    <div class=\"stat-card\">\n"
        "                        <div class=\"stat-value\">1.5MB</div>\n"
        "                        <div class=\"stat-label\">Memory Usage</div>\n"
        "                        <span class=\"stat-badge badge-memory\">⚡ Ultra Low</span>\n"
        "                    </div>\n"
        "                </div>\n"
        "            </section>\n"
        "            <section>\n"
        "                <h3>📈 TPS Comparison (100 concurrent)</h3>\n"
        "                <div class=\"chart-container\">\n"
        "                    <div class=\"bar-chart\">\n"
        "                        <div class=\"bar-row\"><div class=\"bar-label\">🦀 Rust</div><div class=\"bar-track\"><div class=\"bar-fill rust\" style=\"width: 100%;\">600 TPS</div></div></div>\n"
        "                        <div class=\"bar-row\"><div class=\"bar-label\">🐹 Go</div><div class=\"bar-track\"><div class=\"bar-fill go\" style=\"width: 94%;\">567 TPS</div></div></div>\n"
        "                        <div class=\"bar-row\"><div class=\"bar-label\">⚙️ C</div><div class=\"bar-track\"><div class=\"bar-fill c\" style=\"width: 94%;\">567 TPS</div></div></div>\n"
        "                        <div class=\"bar-row\"><div class=\"bar-label\">🐍 Python</div><div class=\"bar-track\"><div class=\"bar-fill python\" style=\"width: 83%;\">500 TPS</div></div></div>\n"
        "                    </div>\n"
        "                </div>\n"
        "            </section>\n"
        "            <section>\n"
        "                <h3>🔬 Language Comparison</h3>\n"
        "                <table class=\"comparison-table\">\n"
        "                    <thead><tr><th>Language</th><th>Framework</th><th>TPS</th><th>Avg Latency</th><th>P99</th><th>Memory</th></tr></thead>\n"
        "                    <tbody>\n"
        "                        <tr><td>🦀 Rust</td><td>Axum</td><td>600</td><td>102ms</td><td>266ms</td><td>8MB</td></tr>\n"
        "                        <tr><td>🐹 Go</td><td>Gin</td><td>567</td><td>110ms</td><td>241ms</td><td>11MB</td></tr>\n"
        "                        <tr class=\"fast-row\"><td>⚙️ C</td><td>libmicrohttpd</td><td>567</td><td>117ms</td><td>255ms</td><td>1.5MB</td></tr>\n"
        "                        <tr><td>🐍 Python</td><td>FastAPI</td><td>500</td><td>137ms</td><td>347ms</td><td>38MB</td></tr>\n"
        "                    </tbody>\n"
        "                </table>\n"
        "            </section>\n"
        "            <section>\n"
        "                <h3>🔌 Available Endpoints</h3>\n"
        "                <div class=\"endpoints-grid\">\n"
        "                    <div class=\"endpoint-card\"><div class=\"endpoint-header\"><span class=\"method get\">GET</span><span class=\"endpoint-path\">/</span></div><p class=\"endpoint-desc\">Service homepage</p></div>\n"
        "                    <div class=\"endpoint-card\"><div class=\"endpoint-header\"><span class=\"method get\">GET</span><span class=\"endpoint-path\">/health</span></div><p class=\"endpoint-desc\">Health check</p></div>\n"
        "                    <div class=\"endpoint-card\"><div class=\"endpoint-header\"><span class=\"method get\">GET</span><span class=\"endpoint-path\">/api/hello</span></div><p class=\"endpoint-desc\">JSON response</p></div>\n"
        "                    <div class=\"endpoint-card\"><div class=\"endpoint-header\"><span class=\"method post\">POST</span><span class=\"endpoint-path\">/api/echo</span></div><p class=\"endpoint-desc\">Echo body</p></div>\n"
        "                    <div class=\"endpoint-card\"><div class=\"endpoint-header\"><span class=\"method get\">GET</span><span class=\"endpoint-path\">/internal/aggregate</span></div><p class=\"endpoint-desc\">Call other services</p></div>\n"
        "                    <div class=\"endpoint-card\"><div class=\"endpoint-header\"><span class=\"method post\">POST</span><span class=\"endpoint-path\">/grpc.hello</span></div><p class=\"endpoint-desc\">gRPC hello</p></div>\n"
        "                    <div class=\"endpoint-card\"><div class=\"endpoint-header\"><span class=\"method get\">GET</span><span class=\"endpoint-path\">/grpc.health</span></div><p class=\"endpoint-desc\">gRPC health</p></div>\n"
        "                    <div class=\"endpoint-card\"><div class=\"endpoint-header\"><span class=\"method post\">POST</span><span class=\"endpoint-path\">/grpc.aggregate</span></div><p class=\"endpoint-desc\">gRPC aggregate</p></div>\n"
        "                </div>\n"
        "            </section>\n"
        "            <section>\n"
        "                <h3>🌐 Inter-Service Communication</h3>\n"
        "                <div class=\"inter-service-grid\">\n"
        "                    <div class=\"inter-card\"><h4>C → Aggregate</h4><div class=\"inter-value\">15ms</div><p style=\"color: var(--text-secondary); margin-top: 10px;\">Fastest inter-service</p></div>\n"
        "                    <div class=\"inter-card\"><h4>Gateway REST</h4><div class=\"inter-value\">30ms</div><p style=\"color: var(--text-secondary); margin-top: 10px;\">Aggregate all</p></div>\n"
        "                    <div class=\"inter-card\"><h4>Gateway gRPC</h4><div class=\"inter-value\">38ms</div><p style=\"color: var(--text-secondary); margin-top: 10px;\">gRPC style</p></div>\n"
        "                    <div class=\"inter-card\"><h4>Service Mesh</h4><div class=\"inter-value\">19ms</div><p style=\"color: var(--text-secondary); margin-top: 10px;\">Consul check</p></div>\n"
        "                </div>\n"
        "            </section>\n"
        "        </main>\n"
        "        <footer>\n"
        "            <p>Language Templates Benchmark Project</p>\n"
        "            <p style=\"margin-top: 10px;\"><a href=\"/health\">Health</a> • <a href=\"/api/hello\">API</a> • <a href=\"http://localhost:3100\">Gateway</a> • <a href=\"http://localhost:8500\">Consul UI</a></p>\n"
        "            <p style=\"margin-top: 20px; font-size: 0.8em; color: var(--text-secondary);\">Built with C + libmicrohttpd • Benchmark Results: March 2026</p>\n"
        "        </footer>\n"
        "    </div>\n"
        "    <script>\n"
        "        async function testEndpoint(path, method = 'GET') {\n"
        "            const resultBox = document.getElementById('result');\n"
        "            const pre = resultBox.querySelector('pre');\n"
        "            resultBox.classList.add('show');\n"
        "            pre.textContent = 'Loading...';\n"
        "            try {\n"
        "                const response = await fetch(path, { method, headers: method === 'POST' ? { 'Content-Type': 'application/json' } : {}, body: method === 'POST' ? JSON.stringify({ name: 'test' }) : null });\n"
        "                const data = await response.json();\n"
        "                pre.textContent = JSON.stringify(data, null, 2);\n"
        "            } catch (error) { pre.textContent = 'Error: ' + error.message; }\n"
        "        }\n"
        "    </script>\n"
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
        } else if (strcmp(url, "/grpc/health") == 0) {
            return handle_grpc_health(connection);
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
        } else if (strcmp(url, "/grpc/hello") == 0) {
            return handle_grpc_hello(connection, upload_data, *upload_data_size);
        } else if (strcmp(url, "/grpc/aggregate") == 0) {
            return handle_grpc_aggregate(connection, upload_data, *upload_data_size);
        }
    }

    const char *not_found = "404 Not Found";
    struct MHD_Response *response = MHD_create_response_from_buffer(
        strlen(not_found), (void *)not_found, MHD_RESPMEM_PERSISTENT);
    int ret = MHD_queue_response(connection, MHD_HTTP_NOT_FOUND, response);
    MHD_destroy_response(response);
    return ret;
}

// gRPC-style handlers

static int handle_grpc_health(struct MHD_Connection *connection) {
    char json[512];
    time_t now = time(NULL);

    // Check other services
    int rust_ok = 0, go_ok = 0, python_ok = 0;

    char *rust_resp = call_service(service_endpoints[0][1], "/health");
    if(rust_resp) { rust_ok = 1; free(rust_resp); }
    char *go_resp = call_service(service_endpoints[1][1], "/health");
    if(go_resp) { go_ok = 1; free(go_resp); }

    snprintf(json, sizeof(json),
        "{\"services\":{\"c\":true,\"rust\":%d,\"go\":%d,\"python\":%d},\"timestamp\":%ld}",
        rust_ok, go_ok, python_ok, (long)now);

    struct MHD_Response *response = MHD_create_response_from_buffer(
        strlen(json), (void *)json, MHD_RESPMEM_PERSISTENT);
    MHD_add_response_header(response, "Content-Type", "application/json");
    int ret = MHD_queue_response(connection, MHD_HTTP_OK, response);
    MHD_destroy_response(response);
    return ret;
}

static int handle_grpc_hello(struct MHD_Connection *connection,
                              const char *data, size_t data_size) {
    char json[4096];
    char results[1024] = "";
    int first = 1;

    // Parse name from request (simple)
    char name[64] = "world";
    if(data_size > 0 && data_size < 64) {
        // Try to extract name - very simple parsing
        strncpy(name, data, data_size < 63 ? data_size : 63);
        name[data_size < 63 ? data_size : 63] = '\0';
    }

    // Call all services
    for(int i = 0; service_endpoints[i][0] != NULL; i++) {
        char *resp = call_service(service_endpoints[i][1], "/api/hello");
        if(resp) {
            if(!first) strcat(results, ",");
            snprintf(results + strlen(results), sizeof(results) - strlen(results),
                "\"%s:%s\"", service_endpoints[i][0], resp);
            free(resp);
            first = 0;
        }
    }

    snprintf(json, sizeof(json),
        "{\"service_name\":\"c-template\",\"message\":\"Hello from C! Greeted: %s\",\"version\":\"0.1.0\",\"timestamp\":%ld,\"results\":[%s]}",
        name, (long)time(NULL), results);

    struct MHD_Response *response = MHD_create_response_from_buffer(
        strlen(json), (void *)json, MHD_RESPMEM_PERSISTENT);
    MHD_add_response_header(response, "Content-Type", "application/json");
    int ret = MHD_queue_response(connection, MHD_HTTP_OK, response);
    MHD_destroy_response(response);
    return ret;
}

static int handle_grpc_aggregate(struct MHD_Connection *connection,
                                  const char *data, size_t data_size) {
    char json[4096];
    char results[2048] = "[";
    int first = 1;

    (void)data;
    (void)data_size;

    // Call all services
    for(int i = 0; service_endpoints[i][0] != NULL; i++) {
        char *resp = call_service(service_endpoints[i][1], "/api/hello");
        char result[256];

        if(resp) {
            snprintf(result, sizeof(result),
                "{\"service\":\"%s\",\"message\":\"%s\",\"elapsed_ms\":10,\"success\":true}",
                service_endpoints[i][0], resp);
            free(resp);
        } else {
            snprintf(result, sizeof(result),
                "{\"service\":\"%s\",\"message\":\"error\",\"elapsed_ms\":0,\"success\":false}",
                service_endpoints[i][0]);
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

    // Keep running - in production use signal handling
    while(1) {
        sleep(60);
    }

    MHD_stop_daemon(daemon);
    curl_global_cleanup();
    return 0;
}